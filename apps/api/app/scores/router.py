"""/v1/couriers/{id}/score — average of ratings from last 90 days."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.core.exceptions import NotFoundError
from app.couriers.models import Courier
from app.db.session import get_session
from app.merchants.models import Merchant
from app.ratings.models import CourierRating

router = APIRouter(prefix="/couriers", tags=["scores"])
admin_router = APIRouter(prefix="/admin/scores", tags=["scores-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

RATING_WINDOW_DAYS = 90


async def _calc_score(session: AsyncSession, courier_id: int) -> dict:
    cutoff = datetime.now(UTC) - timedelta(days=RATING_WINDOW_DAYS)
    row = (
        await session.execute(
            select(
                sa_func.avg(CourierRating.stars).label("avg"),
                sa_func.count(CourierRating.id).label("total"),
            ).where(
                CourierRating.courier_id == courier_id,
                CourierRating.created_at >= cutoff,
            )
        )
    ).first()
    avg = round(float(row.avg), 1) if row and row.avg else 0.0
    total = int(row.total) if row else 0
    return {"avg_stars": avg, "total_ratings": total}


@router.get("/{courier_id}/score")
async def get_my_score(
    courier_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> dict:
    courier = (
        await session.execute(
            select(Courier).where(
                Courier.id == courier_id,
                Courier.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if courier is None:
        raise NotFoundError("Entregador nao encontrado.")
    return await _calc_score(session, courier.id)


@router.get("/{courier_id}/ratings")
async def list_my_ratings(
    courier_id: int,
    user: CurrentUser,
    session: SessionDep,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    courier = (
        await session.execute(
            select(Courier).where(Courier.id == courier_id, Courier.user_id == user.id)
        )
    ).scalar_one_or_none()
    if courier is None:
        raise NotFoundError("Entregador nao encontrado.")
    from sqlalchemy import func
    total = (
        await session.execute(
            select(func.count()).select_from(CourierRating).where(CourierRating.courier_id == courier.id)
        )
    ).scalar() or 0
    rows = (
        await session.execute(
            select(CourierRating, Merchant.trade_name)
            .join(Merchant, CourierRating.merchant_id == Merchant.id)
            .where(CourierRating.courier_id == courier.id)
            .order_by(CourierRating.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return {
        "items": [
            {
                "id": r.id,
                "stars": r.stars,
                "comment": r.comment,
                "merchant_name": trade_name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, trade_name in rows
        ],
        "total": total,
    }


@admin_router.get("/{courier_id}")
async def get_courier_score(
    courier_id: int,
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
) -> dict:
    return await _calc_score(session, courier_id)
