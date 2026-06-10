"""Store-ownership dependency for the deliveries endpoints (A01 / TH-03).

A delivery endpoint is operated by the STORE owner. `merchant_scope` resolves the
authenticated user's merchant (via `merchant_users`) and returns the
`(area_id, merchant_id)` pair the service pushes into every WHERE clause. A user
with no merchant membership → 404 (no existence leak — the surface simply does not
exist for them). The merchant carries its own `area_id`, so isolation is closed by
construction: the store can only ever reach its own area's deliveries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.merchants.models import Merchant, MerchantUser

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass(frozen=True)
class StoreScope:
    """The resolved (area_id, merchant_id) for the authenticated store user."""

    area_id: int
    merchant_id: int
    user_id: int


async def merchant_scope(user: CurrentUser, session: SessionDep) -> StoreScope:
    """Resolve the authenticated user's merchant or 404 (A01 / TH-03)."""
    stmt = (
        select(Merchant)
        .join(MerchantUser, MerchantUser.merchant_id == Merchant.id)
        .where(MerchantUser.user_id == user.id)
    )
    merchant = (await session.execute(stmt)).scalars().first()
    if merchant is None:
        # The store surface does not exist for a non-merchant user — 404, not 403.
        raise NotFoundError("Loja não encontrada.")
    return StoreScope(area_id=merchant.area_id, merchant_id=merchant.id, user_id=user.id)


MerchantScopeDep = Annotated[StoreScope, Depends(merchant_scope)]
