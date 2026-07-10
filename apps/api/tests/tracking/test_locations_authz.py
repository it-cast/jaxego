"""Location ingestion authz (TH-5 / DEC-002): owner-only, in-window-only.

The IDOR barrier (`get_delivery_for_courier`) is exercised directly: courier B
posting on courier A's delivery → 404 (NotFoundError, never 403). The window rule is
exercised via the handler: ACEITA/COLETADA accept; any other state → 409. aware-UTC
is asserted on the stored sample (TD-010). A self-contained seed (two couriers + one
ACEITA delivery assigned to the first) avoids cross-package fixture imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.dispatch.dependencies import CourierScope
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.proofs.service import get_delivery_for_courier
from app.tracking.locations import LocationIn, OutOfTrackingWindowError, ingest_location
from app.tracking.models import DeliveryLocation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

NEAR_LAT, NEAR_LNG = -21.5405, -42.1800


@dataclass
class LocSeed:
    area_id: int
    delivery_id: int
    courier_id: int
    courier_user_id: int
    other_courier_id: int


@pytest_asyncio.fixture
async def loc_seed(session_factory: async_sessionmaker[AsyncSession]) -> LocSeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        u1 = User(
            email="c1@example.com",
            name="C1",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        u2 = User(
            email="c2@example.com",
            name="C2",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add_all([u1, u2])
        await s.flush()
        c1 = Courier(
            area_id=area.id,
            user_id=u1.id,
            cpf="39053344705",
            full_name="C1",
            phone_e164="+5522999990000",
            email="c1@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        c2 = Courier(
            area_id=area.id,
            user_id=u2.id,
            cpf="52998224725",
            full_name="C2",
            phone_e164="+5522999990001",
            email="c2@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        s.add_all([c1, c2])
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
        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=c1.id,
            recipient_id=None,
            state="ACEITA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua A, 1",
            dropoff_address="Rua B, 2",
            dropoff_neighborhood_id=nbhd.id,
            fee_cents=0,
            items_quantity=1,
            public_token="LOCTOKEN000000000000000001",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        await s.commit()
        return LocSeed(
            area_id=area.id,
            delivery_id=delivery.id,
            courier_id=c1.id,
            courier_user_id=u1.id,
            other_courier_id=c2.id,
        )


def _scope(seed: LocSeed, courier_id: int) -> CourierScope:
    return CourierScope(area_id=seed.area_id, courier_id=courier_id, user_id=seed.courier_user_id)


@pytest.mark.asyncio
async def test_owner_in_window_records_aware_utc(
    session_factory: async_sessionmaker[AsyncSession], loc_seed: LocSeed
) -> None:
    async with session_factory() as s:
        await ingest_location(
            loc_seed.delivery_id,
            LocationIn(lat=NEAR_LAT, lng=NEAR_LNG),
            _scope(loc_seed, loc_seed.courier_id),
            s,
        )
    async with session_factory() as s:
        loc = (
            await s.execute(
                select(DeliveryLocation).where(DeliveryLocation.delivery_id == loc_seed.delivery_id)
            )
        ).scalar_one()
        assert loc.lat == NEAR_LAT
        # aware-UTC is written (datetime.now(UTC)); SQLite strips tz on readback, so
        # we coerce via the read-boundary helper and assert it is recent (TD-010).
        from app.db.mixins import ensure_aware_utc

        recorded = ensure_aware_utc(loc.recorded_at)
        assert recorded.tzinfo is not None
        assert (datetime.now(UTC) - recorded).total_seconds() < 60


@pytest.mark.asyncio
async def test_non_owner_gets_404_not_403(
    session_factory: async_sessionmaker[AsyncSession], loc_seed: LocSeed
) -> None:
    """Courier B posting on courier A's delivery → 404 (IDOR closed)."""
    async with session_factory() as s:
        with pytest.raises(NotFoundError):
            await ingest_location(
                loc_seed.delivery_id,
                LocationIn(lat=NEAR_LAT, lng=NEAR_LNG),
                _scope(loc_seed, loc_seed.other_courier_id),
                s,
            )


@pytest.mark.asyncio
async def test_out_of_window_returns_409(
    session_factory: async_sessionmaker[AsyncSession], loc_seed: LocSeed
) -> None:
    """A delivery in ENTREGUE no longer accepts location samples (409)."""
    async with session_factory() as s:
        delivery = await s.get(Delivery, loc_seed.delivery_id)
        delivery.state = "ENTREGUE"
        await s.commit()
    async with session_factory() as s:
        with pytest.raises(OutOfTrackingWindowError):
            await ingest_location(
                loc_seed.delivery_id,
                LocationIn(lat=NEAR_LAT, lng=NEAR_LNG),
                _scope(loc_seed, loc_seed.courier_id),
                s,
            )


@pytest.mark.asyncio
async def test_get_delivery_for_courier_owner_ok(
    session_factory: async_sessionmaker[AsyncSession], loc_seed: LocSeed
) -> None:
    async with session_factory() as s:
        delivery = await get_delivery_for_courier(
            s, delivery_id=loc_seed.delivery_id, courier_id=loc_seed.courier_id
        )
        assert delivery.id == loc_seed.delivery_id
