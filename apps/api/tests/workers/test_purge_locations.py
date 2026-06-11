"""purge_locations (LGPD): hard-delete samples of terminal deliveries >24h old.

A FINALIZADA delivery with a 25h-old sample → purged; a 1h-old sample on the same
delivery → kept; samples on a still-ACTIVE delivery → kept regardless of age.
Idempotent: a second run deletes nothing new.
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
from app.tracking.models import DeliveryLocation
from app.workers.lifecycle import purge_locations
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class PurgeSeed:
    terminal_id: int
    active_id: int


async def _delivery(
    s: AsyncSession, *, area_id: int, merchant_id: int, nbhd_id: int, state: str, token: str
) -> Delivery:
    d = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        state=state,
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
    )
    s.add(d)
    await s.flush()
    return d


@pytest_asyncio.fixture
async def purge_seed(session_factory: async_sessionmaker[AsyncSession]) -> PurgeSeed:
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
        terminal = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            state="FINALIZADA",
            token="TERM00000000000000000000AA",
        )
        active = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            state="COLETADA",
            token="ACT000000000000000000000AA",
        )
        now = datetime.now(UTC)
        s.add_all(
            [
                # terminal: one old (purged), one fresh (kept)
                DeliveryLocation(
                    area_id=area.id,
                    delivery_id=terminal.id,
                    lat=-21.5,
                    lng=-42.1,
                    recorded_at=now - timedelta(hours=25),
                ),
                DeliveryLocation(
                    area_id=area.id,
                    delivery_id=terminal.id,
                    lat=-21.5,
                    lng=-42.1,
                    recorded_at=now - timedelta(hours=1),
                ),
                # active: old sample but delivery not terminal → kept
                DeliveryLocation(
                    area_id=area.id,
                    delivery_id=active.id,
                    lat=-21.5,
                    lng=-42.1,
                    recorded_at=now - timedelta(hours=48),
                ),
            ]
        )
        await s.commit()
        return PurgeSeed(terminal_id=terminal.id, active_id=active.id)


async def _count(session_factory, delivery_id: int) -> int:
    async with session_factory() as s:
        return int(
            (
                await s.execute(
                    select(func.count(DeliveryLocation.id)).where(
                        DeliveryLocation.delivery_id == delivery_id
                    )
                )
            ).scalar_one()
        )


@pytest.mark.asyncio
async def test_purges_old_terminal_keeps_rest(
    session_factory: async_sessionmaker[AsyncSession], purge_seed: PurgeSeed
) -> None:
    ctx = {"session_factory": session_factory}
    purged = await purge_locations(ctx)
    assert purged == 1
    # Terminal: only the fresh sample remains.
    assert await _count(session_factory, purge_seed.terminal_id) == 1
    # Active: untouched regardless of age.
    assert await _count(session_factory, purge_seed.active_id) == 1


@pytest.mark.asyncio
async def test_idempotent(
    session_factory: async_sessionmaker[AsyncSession], purge_seed: PurgeSeed
) -> None:
    ctx = {"session_factory": session_factory}
    assert await purge_locations(ctx) == 1
    assert await purge_locations(ctx) == 0
