"""Store favorites/blocks CRUD (RN-014 / D-06) — service + schemas + router.

The store manages two SEPARATE lists (RN-014): favorites (entered first in the
cascade, ordered by `priority` — D-01; reorderable) and blocks (never offered,
private `reason`). All routes resolve the store via `merchant_scope` (A01 / TH-3):
the (area_id, merchant_id) pair is pushed into every WHERE clause, so a courier
from another area → 404. NO payload includes the courier's location (TH-3). A
store may only favorite/block a courier that ALREADY served it (privacy — no open
marketplace, ADR-007): the courier must have a finished/accepted delivery with the
store. `extra="forbid"` blocks mass assignment (A03).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.couriers.models import Courier
from app.db.session import get_session
from app.deliveries.dependencies import MerchantScopeDep
from app.deliveries.models import Delivery
from app.merchants.models import MerchantCourierBlock, MerchantCourierFavorite

router = APIRouter(prefix="/merchants/dispatch", tags=["merchants-dispatch"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class AlreadyExistsError(AppError):
    """The favorite/block already exists (409)."""

    status_code = 409
    code = "already_exists"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CourierNotServedError(AppError):
    """The courier has never served this store — cannot favorite/block (422)."""

    status_code = 422
    code = "courier_not_served"

    def __init__(self) -> None:
        super().__init__(
            "Você só pode favoritar ou bloquear entregadores que já atenderam sua loja."
        )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class FavoriteCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    courier_id: int


class ReorderBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # The full ordered list of favorite courier ids (top = highest priority).
    courier_ids: list[int] = Field(min_length=1)


class FavoriteRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    courier_id: int
    priority: int
    courier_name: str
    avg_stars: float


class BlockCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    courier_id: int
    reason: str | None = Field(default=None, max_length=255)


class BlockRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    courier_id: int
    courier_name: str
    # The private reason — visible only to the store (RN-014), never the courier.
    reason: str | None
    created_at: str | None


# ---------------------------------------------------------------------------
# Service helpers
# ---------------------------------------------------------------------------
async def _scoped_courier(session: AsyncSession, *, area_id: int, courier_id: int) -> Courier:
    """Load a courier in this area or 404 (no cross-area leak)."""
    courier = (
        await session.execute(
            select(Courier).where(
                Courier.id == courier_id,
                Courier.area_id == area_id,
                Courier.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if courier is None:
        raise NotFoundError("Entregador não encontrado.")
    return courier


async def _assert_served(
    session: AsyncSession, *, area_id: int, merchant_id: int, courier_id: int
) -> None:
    """The courier must have at least one delivery with this store (privacy)."""
    served = (
        await session.execute(
            select(Delivery.id)
            .where(
                Delivery.area_id == area_id,
                Delivery.merchant_id == merchant_id,
                Delivery.courier_id == courier_id,
            )
            .limit(1)
        )
    ).first()
    if served is None:
        raise CourierNotServedError()


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------
@router.get("/favorites", response_model=list[FavoriteRow])
async def list_favorites(scope: MerchantScopeDep, session: SessionDep) -> list[FavoriteRow]:
    """List the store's favorites ordered by priority with avg rating."""
    from sqlalchemy import func as sa_func
    from datetime import UTC, timedelta, datetime
    from app.ratings.models import CourierRating

    rows = (
        await session.execute(
            select(MerchantCourierFavorite, Courier)
            .join(Courier, Courier.id == MerchantCourierFavorite.courier_id)
            .where(
                MerchantCourierFavorite.area_id == scope.area_id,
                MerchantCourierFavorite.merchant_id == scope.merchant_id,
            )
            .order_by(MerchantCourierFavorite.priority, MerchantCourierFavorite.id)
        )
    ).all()

    courier_ids = [fav.courier_id for fav, _ in rows]
    ratings: dict[int, float] = {}
    if courier_ids:
        cutoff = datetime.now(UTC) - timedelta(days=90)
        rating_rows = (await session.execute(
            select(
                CourierRating.courier_id,
                sa_func.avg(CourierRating.stars).label("avg"),
            ).where(
                CourierRating.courier_id.in_(courier_ids),
                CourierRating.created_at >= cutoff,
            ).group_by(CourierRating.courier_id)
        )).all()
        ratings = {int(r.courier_id): round(float(r.avg), 1) for r in rating_rows}

    return [
        FavoriteRow(
            courier_id=fav.courier_id,
            priority=fav.priority,
            courier_name=courier.full_name,
            avg_stars=ratings.get(fav.courier_id, 0.0),
        )
        for fav, courier in rows
    ]


@router.post("/favorites", response_model=FavoriteRow, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    body: FavoriteCreateBody, scope: MerchantScopeDep, session: SessionDep
) -> FavoriteRow:
    """Favorite a courier (must have served the store — privacy). Appended last."""
    courier = await _scoped_courier(session, area_id=scope.area_id, courier_id=body.courier_id)
    await _assert_served(
        session, area_id=scope.area_id, merchant_id=scope.merchant_id, courier_id=body.courier_id
    )
    existing = (
        await session.execute(
            select(MerchantCourierFavorite).where(
                MerchantCourierFavorite.area_id == scope.area_id,
                MerchantCourierFavorite.merchant_id == scope.merchant_id,
                MerchantCourierFavorite.courier_id == body.courier_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AlreadyExistsError("Esse entregador já é favorito.")
    # Append at the end of the priority order.
    max_priority = (
        await session.execute(
            select(MerchantCourierFavorite.priority)
            .where(
                MerchantCourierFavorite.area_id == scope.area_id,
                MerchantCourierFavorite.merchant_id == scope.merchant_id,
            )
            .order_by(MerchantCourierFavorite.priority.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    next_priority = (max_priority + 1) if max_priority is not None else 0
    fav = MerchantCourierFavorite(
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        courier_id=body.courier_id,
        priority=next_priority,
    )
    session.add(fav)
    await session.commit()
    return FavoriteRow(
        courier_id=fav.courier_id,
        priority=fav.priority,
        courier_name=courier.full_name,
        avg_stars=0.0,
    )


@router.put("/favorites/reorder", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def reorder_favorites(
    body: ReorderBody, scope: MerchantScopeDep, session: SessionDep
) -> None:
    """Persist the favorites' priority order (D-01 — cascade order)."""
    favorites = list(
        (
            await session.execute(
                select(MerchantCourierFavorite).where(
                    MerchantCourierFavorite.area_id == scope.area_id,
                    MerchantCourierFavorite.merchant_id == scope.merchant_id,
                )
            )
        )
        .scalars()
        .all()
    )
    by_courier = {f.courier_id: f for f in favorites}
    # Only reorder ids that are actually favorites (ignore strangers silently-safe).
    priority = 0
    for cid in body.courier_ids:
        fav = by_courier.get(cid)
        if fav is not None:
            fav.priority = priority
            priority += 1
    await session.commit()


@router.delete(
    "/favorites/{courier_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def remove_favorite(courier_id: int, scope: MerchantScopeDep, session: SessionDep) -> None:
    """Remove a favorite (the courier can still be reached by ranking)."""
    fav = (
        await session.execute(
            select(MerchantCourierFavorite).where(
                MerchantCourierFavorite.area_id == scope.area_id,
                MerchantCourierFavorite.merchant_id == scope.merchant_id,
                MerchantCourierFavorite.courier_id == courier_id,
            )
        )
    ).scalar_one_or_none()
    if fav is None:
        raise NotFoundError("Favorito não encontrado.")
    await session.delete(fav)
    await session.commit()


# ---------------------------------------------------------------------------
# Blocks (private — RN-014)
# ---------------------------------------------------------------------------
@router.get("/blocks", response_model=list[BlockRow])
async def list_blocks(scope: MerchantScopeDep, session: SessionDep) -> list[BlockRow]:
    """List the store's blocked couriers with the private reason (store-only)."""
    rows = (
        await session.execute(
            select(MerchantCourierBlock, Courier)
            .join(Courier, Courier.id == MerchantCourierBlock.courier_id)
            .where(
                MerchantCourierBlock.area_id == scope.area_id,
                MerchantCourierBlock.merchant_id == scope.merchant_id,
            )
            .order_by(MerchantCourierBlock.created_at.desc())
        )
    ).all()
    return [
        BlockRow(
            courier_id=blk.courier_id,
            courier_name=courier.full_name,
            reason=blk.reason,
            created_at=blk.created_at.isoformat() if blk.created_at else None,
        )
        for blk, courier in rows
    ]


@router.post("/blocks", response_model=BlockRow, status_code=status.HTTP_201_CREATED)
async def add_block(
    body: BlockCreateBody, scope: MerchantScopeDep, session: SessionDep
) -> BlockRow:
    """Block a courier (private — RN-014). Removes any existing favorite."""
    courier = await _scoped_courier(session, area_id=scope.area_id, courier_id=body.courier_id)
    await _assert_served(
        session, area_id=scope.area_id, merchant_id=scope.merchant_id, courier_id=body.courier_id
    )
    existing = (
        await session.execute(
            select(MerchantCourierBlock).where(
                MerchantCourierBlock.area_id == scope.area_id,
                MerchantCourierBlock.merchant_id == scope.merchant_id,
                MerchantCourierBlock.courier_id == body.courier_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AlreadyExistsError("Esse entregador já está bloqueado.")
    # Blocking a favorite removes the favorite (they are mutually exclusive states).
    fav = (
        await session.execute(
            select(MerchantCourierFavorite).where(
                MerchantCourierFavorite.area_id == scope.area_id,
                MerchantCourierFavorite.merchant_id == scope.merchant_id,
                MerchantCourierFavorite.courier_id == body.courier_id,
            )
        )
    ).scalar_one_or_none()
    if fav is not None:
        await session.delete(fav)
    block = MerchantCourierBlock(
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        courier_id=body.courier_id,
        reason=body.reason,
    )
    session.add(block)
    await session.commit()
    return BlockRow(
        courier_id=block.courier_id,
        courier_name=courier.full_name,
        reason=block.reason,
        created_at=block.created_at.isoformat() if block.created_at else None,
    )


@router.delete("/blocks/{courier_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_block(courier_id: int, scope: MerchantScopeDep, session: SessionDep) -> None:
    """Unblock a courier (they may receive offers again)."""
    block = (
        await session.execute(
            select(MerchantCourierBlock).where(
                MerchantCourierBlock.area_id == scope.area_id,
                MerchantCourierBlock.merchant_id == scope.merchant_id,
                MerchantCourierBlock.courier_id == courier_id,
            )
        )
    ).scalar_one_or_none()
    if block is None:
        raise NotFoundError("Bloqueio não encontrado.")
    await session.delete(block)
    await session.commit()


__all__ = ["router"]
