"""Fixtures for the tracking tests (Phase 9, T-05/T-06).

`make_delivery` builds a delivery in a given state with a known public_token, an
assigned courier (so courier PII could leak if the serializer is wrong), a full
dropoff address (so RN-013 can be asserted), and optional location samples. Runs on
the SQLite in-memory DB (no MySQL — the public read has no spatial dependency).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.tracking.models import DeliveryLocation
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_counter = {"n": 0}


def _uniq() -> int:
    _counter["n"] += 1
    return _counter["n"]


async def _base_world(s: AsyncSession) -> tuple[int, int, int]:
    """Area + neighborhood + assigned courier. Returns (area_id, nbhd_id, courier_id)."""
    n = _uniq()
    area = Area(codename=f"area-{n}", name="Pádua", config={})
    s.add(area)
    await s.flush()
    nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
    s.add(nbhd)
    await s.flush()
    user = User(
        email=f"courier-{n}@example.com",
        name="João Entregador",
        password_hash=hash_password("correct-horse-staple-10"),
        platform_role="user",
    )
    s.add(user)
    await s.flush()
    courier = Courier(
        area_id=area.id,
        user_id=user.id,
        cpf=f"{n:011d}",
        full_name="João Entregador",  # would leak if serializer emitted courier name
        phone_e164="+5522999990000",  # would leak if serializer emitted courier phone
        email=f"courier-{n}@example.com",
        kyc_level="simples",
        status="active",
        vehicle_type="moto",
        is_online=True,
        max_concurrent=2,
    )
    s.add(courier)
    await s.flush()
    return area.id, nbhd.id, courier.id


MakeDelivery = Callable[..., Awaitable[Delivery]]


@pytest_asyncio.fixture
async def make_delivery(
    session_factory: async_sessionmaker[AsyncSession],
) -> MakeDelivery:
    async def _make(
        *,
        state: str,
        public_token: str | None = None,
        with_location: bool = False,
    ) -> Delivery:
        n = _uniq()
        async with session_factory() as s:
            area_id, nbhd_id, courier_id = await _base_world(s)
            merchant = Merchant(
                area_id=area_id,
                account_type="cnpj",
                document=f"{n:014d}",
                trade_name="Loja",
                category="restaurante",
                phone_e164=f"+5522{n:09d}",
                email=f"loja-{n}@example.com",
                status="active",
            )
            s.add(merchant)
            await s.flush()
            delivery = Delivery(
                area_id=area_id,
                merchant_id=merchant.id,
                courier_id=courier_id,
                recipient_id=None,
                state=state,
                dispatch_mode="direct",
                payment_method="direct",
                proof_method="photo",
                pickup_address="Rua do Comércio, 100",
                pickup_lat=-21.54,
                pickup_lng=-42.18,
                dropoff_address="Rua das Flores, 200",  # full address (RN-013)
                dropoff_number="200",
                dropoff_complement="ap 3",
                dropoff_neighborhood_id=nbhd_id,
                dropoff_lat=-21.55,
                dropoff_lng=-42.19,
                reference_number="A1B2C3",
                fee_cents=0,
                items_quantity=1,
                public_token=public_token or f"TOKEN{n:020d}",
                origin="manual",
            )
            s.add(delivery)
            await s.flush()
            s.add(
                DeliveryStateTransition(
                    area_id=area_id,
                    delivery_id=delivery.id,
                    from_state=None,
                    to_state=state,
                    created_at=datetime.now(UTC),
                )
            )
            if with_location:
                s.add(
                    DeliveryLocation(
                        area_id=area_id,
                        delivery_id=delivery.id,
                        lat=-21.5405,
                        lng=-42.1805,
                        recorded_at=datetime.now(UTC),
                    )
                )
            await s.commit()
            await s.refresh(delivery)
            return delivery

    return _make
