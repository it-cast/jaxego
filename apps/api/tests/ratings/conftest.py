"""Fixtures for the ratings tests (Phase 13).

Builds a minimal FINALIZADA delivery world: an area, a store (merchant), an active
courier, a dropoff neighborhood, and one delivery in a chosen state. Runs against the
SQLite in-memory DB (Layer 2 of tests/conftest.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest_asyncio
from app.areas.models import Area
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.helpers import make_team

PASSWORD = "correct-horse-staple-10"


@dataclass
class RatingWorld:
    area_a_id: int
    area_b_id: int
    merchant_id: int
    other_merchant_id: int
    courier_id: int
    delivery_id: int  # FINALIZADA, owned by merchant_id


async def _make_delivery(
    s: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    courier_id: int | None,
    nbhd_id: int,
    state: str,
    token: str,
) -> Delivery:
    d = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        courier_id=courier_id,
        state=state,
        pickup_address="Rua A, 1",
        dropoff_address="Rua B, 2",
        dropoff_neighborhood_id=nbhd_id,
        public_token=token,
    )
    s.add(d)
    await s.flush()
    return d


@pytest_asyncio.fixture
async def rating_world(
    session_factory: async_sessionmaker[AsyncSession],
) -> RatingWorld:
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()

        # Desde dd23333: loja e entregador são as próprias contas (sem `users`)
        merchant = Merchant(
            area_id=area_a.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja do Bairro",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            password_hash=hash_password(PASSWORD),
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

        courier = Courier(
            area_id=area_a.id,
            team_id=(await make_team(s, area_id=area_a.id)).id,
            password_hash=hash_password(PASSWORD),
            cpf="39053344705",
            full_name="João Entregador",
            phone_e164="+5522999990000",
            email="courier@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
        )
        s.add(courier)
        await s.flush()

        nbhd = Neighborhood(area_id=area_a.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()

        delivery = await _make_delivery(
            s,
            area_id=area_a.id,
            merchant_id=merchant.id,
            courier_id=courier.id,
            nbhd_id=nbhd.id,
            state="FINALIZADA",
            token="tok_finalizada_01",
        )

        await s.commit()
        return RatingWorld(
            area_a_id=area_a.id,
            area_b_id=area_b.id,
            merchant_id=merchant.id,
            other_merchant_id=other_merchant.id,
            courier_id=courier.id,
            delivery_id=delivery.id,
        )
