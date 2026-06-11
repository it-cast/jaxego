"""Courier-ownership dependency for the dispatch endpoints (A01 / TH-4).

The offer/accept/decline endpoints are operated by the COURIER. `courier_scope`
resolves the authenticated user's courier (active, not deleted) and returns the
`(area_id, courier_id)` the service pushes into every WHERE clause. A user with no
courier membership → 404 (no existence leak). The courier carries its own
`area_id`, so isolation is closed by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.exceptions import NotFoundError
from app.couriers.models import Courier
from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass(frozen=True)
class CourierScope:
    """The resolved (area_id, courier_id) for the authenticated courier user."""

    area_id: int
    courier_id: int
    user_id: int


async def courier_scope(user: CurrentUser, session: SessionDep) -> CourierScope:
    """Resolve the authenticated user's courier or 404 (A01 / TH-4)."""
    stmt = select(Courier).where(Courier.user_id == user.id, Courier.deleted_at.is_(None))
    courier = (await session.execute(stmt)).scalars().first()
    if courier is None:
        # The courier surface does not exist for a non-courier user — 404, not 403.
        raise NotFoundError("Entregador não encontrado.")
    return CourierScope(area_id=courier.area_id, courier_id=courier.id, user_id=user.id)


CourierScopeDep = Annotated[CourierScope, Depends(courier_scope)]
