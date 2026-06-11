"""Fixtures for the public-API + webhook tests (Phase 12).

Builds a full delivery-creation world (area, store with `external_ref`, Free
subscription, two catalog neighborhoods, an ONLINE courier pricing the trip) plus
an active `ApiKey` for the area AND a second area with its own key+store for the
cross-area IDOR tests. Everything runs against the SQLite in-memory DB (Layer 2).
The fixture returns the FULL token (`jxg_<key_id>_<secret>`) so the tests can call
the public endpoint with a real header.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest_asyncio
from app.api_keys import service as api_key_service
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable
from app.merchants.models import Merchant, MerchantSubscription, MerchantUser
from app.neighborhoods.models import Neighborhood
from app.plans.models import SubscriptionPlan
from app.plans.service import seed_plans_if_missing
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PASSWORD = "correct-horse-staple-10"


@dataclass
class PublicApiSeed:
    """Seeded world for the public-API tests."""

    area_a_id: int
    area_b_id: int
    merchant_id: int
    merchant_external_ref: str
    other_merchant_id: int
    other_merchant_external_ref: str
    dropoff_nbhd_id: int
    # Area A key (active) — full token + handles.
    token: str
    key_id: str
    api_key_id: int
    # Area B key (active) — for cross-area isolation.
    token_b: str
    # Area A admin JWT (for the admin-router tests — RBAC admin_area).
    admin_a_jwt: str
    # Area B admin JWT (cross-area IDOR tests).
    admin_b_jwt: str


async def _make_neighborhood(s: AsyncSession, *, area_id: int, name: str) -> Neighborhood:
    nbhd = Neighborhood(area_id=area_id, name=name, is_informal=False)
    s.add(nbhd)
    await s.flush()
    return nbhd


async def _make_courier_online(
    s: AsyncSession, *, area_id: int, user_id: int, dropoff_id: int, price: Decimal
) -> Courier:
    courier = Courier(
        area_id=area_id,
        user_id=user_id,
        cpf="39053344705",
        full_name="João Entregador",
        phone_e164="+5522999990000",
        email=f"entregador{area_id}@example.com",
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
                area_id=area_id, courier_id=courier.id, neighborhood_id=dropoff_id, kind="include"
            ),
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


async def _make_store(
    s: AsyncSession,
    *,
    area_id: int,
    plan_id: int,
    email: str,
    document: str,
    phone: str,
    external_ref: str,
) -> Merchant:
    owner = User(
        email=email,
        name="Dona da Loja",
        password_hash=hash_password(PASSWORD),
        platform_role="user",
    )
    s.add(owner)
    await s.flush()
    merchant = Merchant(
        area_id=area_id,
        account_type="cnpj",
        document=document,
        trade_name="Loja",
        category="restaurante",
        phone_e164=phone,
        email=email,
        status="active",
        external_ref=external_ref,
    )
    s.add(merchant)
    await s.flush()
    s.add_all(
        [
            MerchantUser(merchant_id=merchant.id, user_id=owner.id, role="owner"),
            MerchantSubscription(
                area_id=area_id, merchant_id=merchant.id, plan_id=plan_id, status="active"
            ),
        ]
    )
    await s.flush()
    return merchant


@pytest_asyncio.fixture
async def public_api_seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> PublicApiSeed:
    """Seed two areas, each with a store (external_ref), a courier, and an API key."""
    # Clear any cached keys from a prior test (in-process auth cache).
    from app.api_keys.dependencies import invalidate_api_key_cache

    invalidate_api_key_cache()

    async with session_factory() as s:
        await seed_plans_if_missing(s)
        free_plan = (
            await s.execute(select(SubscriptionPlan).where(SubscriptionPlan.is_free.is_(True)))
        ).scalar_one()

        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()

        merchant = await _make_store(
            s,
            area_id=area_a.id,
            plan_id=free_plan.id,
            email="loja@example.com",
            document="11222333000181",
            phone="+5522999991111",
            external_ref="MENU-CERTO-001",
        )
        other_merchant = await _make_store(
            s,
            area_id=area_b.id,
            plan_id=free_plan.id,
            email="loja.b@example.com",
            document="11222333000262",
            phone="+5522999992222",
            external_ref="MENU-CERTO-B-001",
        )

        dropoff = await _make_neighborhood(s, area_id=area_a.id, name="Aldeia")
        courier_user_a = User(
            email="cuser.a@example.com",
            name="C",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add(courier_user_a)
        await s.flush()
        await _make_courier_online(
            s, area_id=area_a.id, user_id=courier_user_a.id, dropoff_id=dropoff.id,
            price=Decimal("10.00"),
        )

        api_key, token = await api_key_service.create_api_key(
            s, area_id=area_a.id, name="Menu Certo", scopes=["deliveries:write"]
        )
        _key_b, token_b = await api_key_service.create_api_key(
            s, area_id=area_b.id, name="Menu Certo B", scopes=["deliveries:write"]
        )

        # Area admins (owner membership) — for the admin-router RBAC tests.
        from app.areas.models import AreaAdmin
        from app.core.security import encode_access

        admin_a = User(
            email="admin.a@example.com",
            name="Admin A",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        admin_b = User(
            email="admin.b@example.com",
            name="Admin B",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add_all([admin_a, admin_b])
        await s.flush()
        s.add_all(
            [
                AreaAdmin(area_id=area_a.id, user_id=admin_a.id, role="owner"),
                AreaAdmin(area_id=area_b.id, user_id=admin_b.id, role="owner"),
            ]
        )
        await s.commit()

        admin_a_jwt = encode_access(admin_a.id, area_a.id, "admin_area")
        admin_b_jwt = encode_access(admin_b.id, area_b.id, "admin_area")

        return PublicApiSeed(
            area_a_id=area_a.id,
            area_b_id=area_b.id,
            merchant_id=merchant.id,
            merchant_external_ref="MENU-CERTO-001",
            other_merchant_id=other_merchant.id,
            other_merchant_external_ref="MENU-CERTO-B-001",
            dropoff_nbhd_id=dropoff.id,
            token=token,
            key_id=api_key.key_id,
            api_key_id=api_key.id,
            token_b=token_b,
            admin_a_jwt=admin_a_jwt,
            admin_b_jwt=admin_b_jwt,
        )
