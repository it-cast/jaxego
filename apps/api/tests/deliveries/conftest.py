"""Fixtures for the deliveries tests (Phase 7).

Everything runs against the SQLite in-memory DB (Layer 2 of tests/conftest.py).
A `delivery_seed` builds: an area, a store owner User + Merchant + MerchantUser
(so the `merchant_scope` dependency resolves), a Free subscription, two catalog
neighborhoods (pickup + dropoff), and an ONLINE active courier whose coverage
includes BOTH neighborhoods and whose pricing table prices the trip. This is the
minimal world the create/estimate/limit/isolation tests compose.

The MySQL-only acceptance tests (trigger append-only, FOR UPDATE concurrency,
migration 0006) are marked `@pytest.mark.mysql` and skipped in dev via
`-m "not mysql"`; they run against MySQL 8 live.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable
from app.merchants.models import Merchant, MerchantSubscription, MerchantUser
from app.neighborhoods.models import Neighborhood
from app.plans.service import seed_plans_if_missing
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PASSWORD = "correct-horse-staple-10"


@dataclass
class DeliverySeed:
    """Seeded world for the delivery tests."""

    area_a_id: int
    area_b_id: int
    owner_user_id: int
    owner_email: str
    merchant_id: int
    # Another store (area B) for the IDOR/isolation tests.
    other_owner_user_id: int
    other_owner_email: str
    other_merchant_id: int
    pickup_nbhd_id: int
    dropoff_nbhd_id: int
    courier_id: int
    password: str


async def _make_neighborhood(s: AsyncSession, *, area_id: int, name: str) -> Neighborhood:
    nbhd = Neighborhood(area_id=area_id, name=name, is_informal=False)
    s.add(nbhd)
    await s.flush()
    return nbhd


async def _make_courier_online(
    s: AsyncSession,
    *,
    area_id: int,
    user_id: int,
    pickup_id: int,
    dropoff_id: int,
    price: Decimal,
) -> Courier:
    """An ONLINE, active courier covering pickup+dropoff with a per-neighborhood price."""
    courier = Courier(
        area_id=area_id,
        user_id=user_id,
        cpf="39053344705",
        full_name="João Entregador",
        phone_e164="+5522999990000",
        email="entregador@example.com",
        kyc_level="simples",
        status="active",
        vehicle_type="moto",
        is_online=True,
        max_concurrent=2,
    )
    s.add(courier)
    await s.flush()
    s.add_all(
        [
            CourierCoverageArea(
                area_id=area_id, courier_id=courier.id, neighborhood_id=pickup_id, kind="include"
            ),
            CourierCoverageArea(
                area_id=area_id, courier_id=courier.id, neighborhood_id=dropoff_id, kind="include"
            ),
            # Per-neighborhood price for the dropoff trip (mode 'neighborhood').
            CourierPricingTable(
                area_id=area_id,
                courier_id=courier.id,
                mode="neighborhood",
                neighborhood_id=dropoff_id,
                price=price,
            ),
        ]
    )
    await s.flush()
    return courier


@pytest_asyncio.fixture
async def delivery_seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> DeliverySeed:
    """Seed the full delivery world (store, Free sub, neighborhoods, online courier)."""
    async with session_factory() as s:
        await seed_plans_if_missing(s)
        free_plan = (
            await s.execute(select(__import_plan()).where(__import_plan().is_free.is_(True)))
        ).scalar_one()

        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()

        owner = User(
            email="loja@example.com",
            name="Dona da Loja",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        other_owner = User(
            email="loja.b@example.com",
            name="Outra Loja",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        courier_user = User(
            email="entregador@example.com",
            name="João Entregador",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add_all([owner, other_owner, courier_user])
        await s.flush()

        merchant = Merchant(
            area_id=area_a.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja do Bairro",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        other_merchant = Merchant(
            area_id=area_b.id,
            account_type="cnpj",
            document="11222333000262",
            trade_name="Loja B",
            category="restaurante",
            phone_e164="+5522999992222",
            email="loja.b@example.com",
            status="active",
        )
        s.add_all([merchant, other_merchant])
        await s.flush()

        s.add_all(
            [
                MerchantUser(merchant_id=merchant.id, user_id=owner.id, role="owner"),
                MerchantUser(
                    merchant_id=other_merchant.id, user_id=other_owner.id, role="owner"
                ),
                MerchantSubscription(
                    area_id=area_a.id,
                    merchant_id=merchant.id,
                    plan_id=free_plan.id,
                    status="active",
                ),
                MerchantSubscription(
                    area_id=area_b.id,
                    merchant_id=other_merchant.id,
                    plan_id=free_plan.id,
                    status="active",
                ),
            ]
        )

        pickup = await _make_neighborhood(s, area_id=area_a.id, name="Centro")
        dropoff = await _make_neighborhood(s, area_id=area_a.id, name="Aldeia")
        courier = await _make_courier_online(
            s,
            area_id=area_a.id,
            user_id=courier_user.id,
            pickup_id=pickup.id,
            dropoff_id=dropoff.id,
            price=Decimal("10.00"),
        )

        await s.commit()
        return DeliverySeed(
            area_a_id=area_a.id,
            area_b_id=area_b.id,
            owner_user_id=owner.id,
            owner_email=owner.email,
            merchant_id=merchant.id,
            other_owner_user_id=other_owner.id,
            other_owner_email=other_owner.email,
            other_merchant_id=other_merchant.id,
            pickup_nbhd_id=pickup.id,
            dropoff_nbhd_id=dropoff.id,
            courier_id=courier.id,
            password=PASSWORD,
        )


def __import_plan():
    """Lazy import to avoid circulars at module import time."""
    from app.plans.models import SubscriptionPlan

    return SubscriptionPlan
