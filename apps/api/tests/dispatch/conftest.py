"""Fixtures for the dispatch tests (Phase 8 — F-05).

Two Redis layers (LOW-2):
- `fake_redis` — fakeredis (in-memory, no server) for the NON-concurrent paths
  (offer TTL, privacy, eligibility, cascade, push). Fast and deterministic.
- the REAL Redis lock fidelity needed for the 2-accept race is exercised by the
  `@pytest.mark.mysql` test (MySQL FOR UPDATE + real Redis), run live.

`dispatch_seed` builds an area, a store (Merchant + owner), two catalog
neighborhoods, a delivery in CRIADA, and SEVERAL online couriers (a favorite, a
plain eligible one, a blocked one, one out of coverage). Each is wired so
`build_candidates` can be asserted directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable
from app.deliveries.models import Delivery, Recipient
from app.merchants.models import (
    Merchant,
    MerchantCourierBlock,
    MerchantCourierFavorite,
    MerchantUser,
)
from app.neighborhoods.models import Neighborhood
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PASSWORD = "correct-horse-staple-10"


@dataclass
class DispatchSeed:
    """Seeded world for the dispatch tests."""

    area_id: int
    merchant_id: int
    owner_user_id: int
    pickup_nbhd_id: int
    dropoff_nbhd_id: int
    delivery_id: int
    # Couriers (user_id, courier_id) by role.
    favorite_courier_id: int
    plain_courier_id: int
    blocked_courier_id: int
    uncovered_courier_id: int
    favorite_user_id: int
    plain_user_id: int


@pytest_asyncio.fixture
async def fake_redis():
    """In-memory fakeredis async client (no server). Flushed per test."""
    import fakeredis.aioredis as fakeredis

    client = fakeredis.FakeRedis(decode_responses=True)
    await client.flushall()
    yield client
    await client.aclose()


async def _courier(
    s: AsyncSession,
    *,
    area_id: int,
    user_id: int,
    cpf: str,
    name: str,
    phone: str,
    email: str,
    online: bool = True,
) -> Courier:
    courier = Courier(
        area_id=area_id,
        user_id=user_id,
        cpf=cpf,
        full_name=name,
        phone_e164=phone,
        email=email,
        kyc_level="simples",
        status="active",
        vehicle_type="moto",
        vehicle_plate="ABC1D23",
        is_online=online,
    )
    s.add(courier)
    await s.flush()
    return courier


async def _cover_and_price(
    s: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
    nbhd_ids: list[int],
    dropoff_id: int,
    price: Decimal = Decimal("10.00"),
) -> None:
    for nid in nbhd_ids:
        s.add(
            CourierCoverageArea(
                area_id=area_id, courier_id=courier_id, neighborhood_id=nid, kind="include"
            )
        )
    s.add(
        CourierPricingTable(
            area_id=area_id,
            courier_id=courier_id,
            mode="neighborhood",
            neighborhood_id=dropoff_id,
            price=price,
        )
    )
    await s.flush()


@pytest_asyncio.fixture
async def dispatch_seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> DispatchSeed:
    """Seed area + store + CRIADA delivery + 4 couriers (favorite/plain/blocked/uncovered)."""
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={"max_entregas_simultaneas": 2})
        s.add(area)
        await s.flush()

        owner = User(
            email="loja@example.com",
            name="Loja",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        u_fav = User(
            email="fav@example.com",
            name="Favorito",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        u_plain = User(
            email="plain@example.com",
            name="Plain",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        u_blocked = User(
            email="blocked@example.com",
            name="Blocked",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        u_unc = User(
            email="unc@example.com",
            name="Uncovered",
            password_hash=hash_password(PASSWORD),
            platform_role="user",
        )
        s.add_all([owner, u_fav, u_plain, u_blocked, u_unc])
        await s.flush()

        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Pizzaria do José",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()
        s.add(MerchantUser(merchant_id=merchant.id, user_id=owner.id, role="owner"))

        pickup = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        dropoff = Neighborhood(area_id=area.id, name="Vila Nova", is_informal=False)
        s.add_all([pickup, dropoff])
        await s.flush()

        fav = await _courier(
            s,
            area_id=area.id,
            user_id=u_fav.id,
            cpf="39053344705",
            name="Ana Favorita",
            phone="+5522999990001",
            email="fav@example.com",
        )
        plain = await _courier(
            s,
            area_id=area.id,
            user_id=u_plain.id,
            cpf="11144477735",
            name="Beto Comum",
            phone="+5522999990002",
            email="plain@example.com",
        )
        blocked = await _courier(
            s,
            area_id=area.id,
            user_id=u_blocked.id,
            cpf="52998224725",
            name="Caio Bloqueado",
            phone="+5522999990003",
            email="blocked@example.com",
        )
        uncovered = await _courier(
            s,
            area_id=area.id,
            user_id=u_unc.id,
            cpf="15350946056",
            name="Davi Fora",
            phone="+5522999990004",
            email="unc@example.com",
        )
        for c in (fav, plain, blocked):
            await _cover_and_price(
                s,
                area_id=area.id,
                courier_id=c.id,
                nbhd_ids=[pickup.id, dropoff.id],
                dropoff_id=dropoff.id,
            )
        # Uncovered: covers only pickup (not dropoff) → never eligible.
        await _cover_and_price(
            s,
            area_id=area.id,
            courier_id=uncovered.id,
            nbhd_ids=[pickup.id],
            dropoff_id=dropoff.id,
        )

        # Favorite + block rows.
        s.add(
            MerchantCourierFavorite(
                area_id=area.id, merchant_id=merchant.id, courier_id=fav.id, priority=0
            )
        )
        s.add(
            MerchantCourierBlock(
                area_id=area.id,
                merchant_id=merchant.id,
                courier_id=blocked.id,
                reason="atraso recorrente",
            )
        )

        recipient = Recipient(
            area_id=area.id,
            name="Cliente",
            phone_e164="+5522988887777",
            deliveries_count=0,
            refusals_count=0,
        )
        s.add(recipient)
        await s.flush()

        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=None,
            recipient_id=recipient.id,
            state="CRIADA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua das Flores, 123",
            pickup_neighborhood="Centro",
            dropoff_address="Rua Secreta, 999",
            dropoff_number="999",
            dropoff_complement="ap 2",
            dropoff_neighborhood_id=dropoff.id,
            distance_m=2800,
            estimate_min_cents=1000,
            estimate_max_cents=1000,
            fee_cents=0,
            items_quantity=1,
            public_token="TESTTOKEN0000000000000000A",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        delivery_id = delivery.id

        await s.commit()
        return DispatchSeed(
            area_id=area.id,
            merchant_id=merchant.id,
            owner_user_id=owner.id,
            pickup_nbhd_id=pickup.id,
            dropoff_nbhd_id=dropoff.id,
            delivery_id=delivery_id,
            favorite_courier_id=fav.id,
            plain_courier_id=plain.id,
            blocked_courier_id=blocked.id,
            uncovered_courier_id=uncovered.id,
            favorite_user_id=u_fav.id,
            plain_user_id=u_plain.id,
        )


# Re-export the pytest marker symbol for clarity in test modules.
mysql = pytest.mark.mysql
