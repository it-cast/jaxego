"""absent_timeout (D-07 E2): 'ausente' >10min → enable return; idempotent.

A COLETADA delivery whose notes carry 'absent' and was collected >10min ago gets the
'[return_enabled]' marker appended once; a fresh one (1min) does not; a second run does
not duplicate the marker.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.deliveries.models import Delivery
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.workers.lifecycle import absent_timeout
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class AbsentSeed:
    old_id: int
    fresh_id: int


async def _delivery(
    s: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    nbhd_id: int,
    token: str,
    collected_min_ago: float,
    notes: str,
) -> Delivery:
    d = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        state="COLETADA",
        dispatch_mode="direct",
        payment_method="direct",
        proof_method="photo",
        pickup_address="a",
        dropoff_address="b",
        dropoff_neighborhood_id=nbhd_id,
        fee_cents=0,
        items_quantity=1,
        public_token=token,
        origin="manual",
        notes=notes,
        collected_at=datetime.now(UTC) - timedelta(minutes=collected_min_ago),
    )
    s.add(d)
    await s.flush()
    return d


@pytest_asyncio.fixture
async def absent_seed(session_factory: async_sessionmaker[AsyncSession]) -> AbsentSeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        old = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            token="ABSOLD0000000000000000000A",
            collected_min_ago=15,
            notes="destinatário absent",
        )
        fresh = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            token="ABSFRESH00000000000000000A",
            collected_min_ago=1,
            notes="destinatário absent",
        )
        await s.commit()
        return AbsentSeed(old_id=old.id, fresh_id=fresh.id)


@pytest.mark.asyncio
async def test_enables_return_after_10min(
    session_factory: async_sessionmaker[AsyncSession], absent_seed: AbsentSeed
) -> None:
    ctx = {"session_factory": session_factory}
    count = await absent_timeout(ctx)
    assert count == 1
    async with session_factory() as s:
        assert "[return_enabled]" in (await s.get(Delivery, absent_seed.old_id)).notes
        assert "[return_enabled]" not in ((await s.get(Delivery, absent_seed.fresh_id)).notes or "")


@pytest.mark.asyncio
async def test_idempotent(
    session_factory: async_sessionmaker[AsyncSession], absent_seed: AbsentSeed
) -> None:
    ctx = {"session_factory": session_factory}
    assert await absent_timeout(ctx) == 1
    assert await absent_timeout(ctx) == 0
    async with session_factory() as s:
        notes = (await s.get(Delivery, absent_seed.old_id)).notes
        assert notes.count("[return_enabled]") == 1  # not duplicated
