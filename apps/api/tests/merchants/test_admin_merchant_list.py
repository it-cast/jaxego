"""Area-admin store list (F2.4 / MR-2). Area-scoped (TH-09) + platform bypass."""

from __future__ import annotations

import pytest
from app.areas.models import Area
from app.merchants.models import Merchant
from app.merchants.service import list_area_merchants
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio


async def _merchant(s: AsyncSession, area_id: int, doc: str, status: str = "active") -> Merchant:
    m = Merchant(
        area_id=area_id,
        account_type="cnpj",
        document=doc,
        trade_name="Loja",
        category="restaurante",
        phone_e164=f"+55229{doc[-8:]}",
        email=f"{doc}@example.com",
        status=status,
    )
    s.add(m)
    await s.flush()
    return m


async def test_list_scoped_and_bypass(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()
        await _merchant(s, area_a.id, "11222333000181")
        await _merchant(s, area_a.id, "11222333000262", status="pending_payment")
        await _merchant(s, area_b.id, "11222333000343")
        await s.commit()

        _, total_a = await list_area_merchants(s, area_id=area_a.id)
        assert total_a == 2
        _, active_a = await list_area_merchants(s, area_id=area_a.id, status="active")
        assert active_a == 1
        _, total_all = await list_area_merchants(s, area_id=None)
        assert total_all == 3
