"""/v1/scores + /v1/admin/scores endpoints (REQ-020 / ADR-013 — read-only, TH-05).

There is NO write endpoint for a score (TH-05 — a note cannot be set by hand; it is
derived by the daily job). Two reads:

- `GET /v1/couriers/{courier_id}/score` — the courier sees their OWN latest snapshot
  (ownership enforced: the courier row must belong to the caller's user).
- `GET /v1/admin/scores/{courier_id}` — the area admin sees the breakdown for any
  courier in their area (area in the WHERE clause — TH-03 → 404 outside scope).

The breakdown (component → raw → weight → contribution) is the explainability
requirement (ADR-013). No PII is in the response (only the score math).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.core.exceptions import NotFoundError
from app.couriers.models import Courier
from app.db.session import get_session
from app.scores import service
from app.scores.schemas import CourierScoreRead

router = APIRouter(prefix="/couriers", tags=["scores"])
admin_router = APIRouter(prefix="/admin/scores", tags=["scores-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _to_read(snapshot) -> CourierScoreRead:  # noqa: ANN001 — ORM row
    return CourierScoreRead(
        courier_id=snapshot.courier_id,
        snapshot_date=snapshot.snapshot_date,
        total_score=float(snapshot.total_score),
        level=snapshot.level,
        components=snapshot.components,
    )


@router.get("/{courier_id}/score", response_model=CourierScoreRead)
async def get_my_score(
    courier_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> CourierScoreRead:
    """The courier's OWN latest snapshot. Ownership in the WHERE clause (→ 404)."""
    # The courier row must belong to the caller — ownership is part of the query.
    courier = (
        await session.execute(
            select(Courier).where(
                Courier.id == courier_id,
                Courier.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if courier is None:
        raise NotFoundError("Entregador não encontrado.")
    snapshot = await service.latest_snapshot(session, courier_id=courier.id)
    if snapshot is None:
        raise NotFoundError("Score ainda não calculado.")
    return _to_read(snapshot)


@admin_router.get("/{courier_id}", response_model=CourierScoreRead)
async def get_courier_score(
    courier_id: int,
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
) -> CourierScoreRead:
    """Area admin sees a courier's breakdown. Area in the WHERE clause (TH-03 → 404)."""
    snapshot = await service.latest_snapshot(session, courier_id=courier_id, area_id=scope)
    if snapshot is None:
        raise NotFoundError("Score não encontrado.")
    return _to_read(snapshot)
