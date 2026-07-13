"""Store-ownership dependency for the deliveries endpoints (A01 / TH-03).

A delivery endpoint is operated by the STORE owner. Pós-remoção da tabela
`users`, o ator autenticado do tipo `merchant` É a própria loja — o scope sai
direto do token, sem join de associação. Um ator de outro tipo → 404 (no
existence leak — the surface simply does not exist for them). The merchant
carries its own `area_id`, so isolation is closed by construction.
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
class StoreScope:
    """The resolved (area_id, merchant_id) for the authenticated store actor."""

    area_id: int
    merchant_id: int
    user_id: int  # compat: id do ator (== merchant_id)


async def merchant_scope(user: CurrentUser, session: SessionDep) -> StoreScope:
    """Resolve the authenticated merchant or 404 (A01 / TH-03)."""
    if user.type != "merchant" or user.area_id is None:
        # The store surface does not exist for a non-merchant actor — 404, not 403.
        raise NotFoundError("Loja não encontrada.")
    return StoreScope(area_id=user.area_id, merchant_id=user.id, user_id=user.id)


MerchantScopeDep = Annotated[StoreScope, Depends(merchant_scope)]
