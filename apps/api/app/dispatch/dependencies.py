"""Courier-ownership dependency for the dispatch endpoints (A01 / TH-4).

The offer/accept/decline endpoints are operated by the COURIER. Pós-remoção da
tabela `users`, o ator autenticado do tipo `courier` É o próprio entregador —
o scope sai direto do token. Outro tipo de ator → 404 (no existence leak).
The courier carries its own `area_id`, so isolation is closed by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.exceptions import NotFoundError
from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass(frozen=True)
class CourierScope:
    """The resolved (area_id, courier_id) for the authenticated courier actor."""

    area_id: int
    courier_id: int
    user_id: int  # compat: id do ator (== courier_id)


async def courier_scope(user: CurrentUser, session: SessionDep) -> CourierScope:
    """Resolve the authenticated courier or 404 (A01 / TH-4)."""
    if user.type != "courier" or user.area_id is None:
        # The courier surface does not exist for a non-courier actor — 404, not 403.
        raise NotFoundError("Entregador não encontrado.")
    return CourierScope(area_id=user.area_id, courier_id=user.id, user_id=user.id)


CourierScopeDep = Annotated[CourierScope, Depends(courier_scope)]
