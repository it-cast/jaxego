"""finalize_deliveries (D-06): ENTREGUE >24h with no open dispute → FINALIZADA.

A delivery ENTREGUE 25h ago finalises; one ENTREGUE 1h ago does not; one with an open
dispute does not (mediação Phase 11). Idempotent: a second run finalises nothing new.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.couriers.models import Courier
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.payments_direct.models import PaymentDispute
from app.workers.lifecycle import finalize_deliveries
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class FinSeed:
    old_id: int
    fresh_id: int
    disputed_id: int


async def _delivery(
    s: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    courier_id: int,
    nbhd_id: int,
    token: str,
    delivered_hours_ago: float,
) -> Delivery:
    d = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        courier_id=courier_id,
        state="ENTREGUE",
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
        delivered_at=datetime.now(UTC) - timedelta(hours=delivered_hours_ago),
    )
    s.add(d)
    await s.flush()
    s.add(
        DeliveryStateTransition(
            area_id=area_id,
            delivery_id=d.id,
            from_state="COLETADA",
            to_state="ENTREGUE",
            created_at=datetime.now(UTC),
        )
    )
    return d


@pytest_asyncio.fixture
async def fin_seed(session_factory: async_sessionmaker[AsyncSession]) -> FinSeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        from app.auth.models import User
        from app.core.security import hash_password

        u = User(
            email="c@e.com",
            name="C",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add(u)
        await s.flush()
        courier = Courier(
            area_id=area.id,
            user_id=u.id,
            cpf="39053344705",
            full_name="C",
            phone_e164="+5522999990000",
            email="c@e.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
        )
        s.add(courier)
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
            courier_id=courier.id,
            nbhd_id=nbhd.id,
            token="OLD0000000000000000000000A",
            delivered_hours_ago=25,
        )
        fresh = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=courier.id,
            nbhd_id=nbhd.id,
            token="FRESH00000000000000000000A",
            delivered_hours_ago=1,
        )
        disputed = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=courier.id,
            nbhd_id=nbhd.id,
            token="DISP000000000000000000000A",
            delivered_hours_ago=25,
        )
        s.add(
            PaymentDispute(
                area_id=area.id,
                delivery_id=disputed.id,
                courier_id=courier.id,
                status="open",
                reason="x",
                opened_at=datetime.now(UTC),
            )
        )
        await s.commit()
        return FinSeed(old_id=old.id, fresh_id=fresh.id, disputed_id=disputed.id)


@pytest.mark.asyncio
async def test_finalizes_only_old_undisputed(
    session_factory: async_sessionmaker[AsyncSession], fin_seed: FinSeed
) -> None:
    ctx = {"session_factory": session_factory}
    count = await finalize_deliveries(ctx)
    assert count == 1
    async with session_factory() as s:
        assert (await s.get(Delivery, fin_seed.old_id)).state == "FINALIZADA"
        assert (await s.get(Delivery, fin_seed.fresh_id)).state == "ENTREGUE"
        assert (await s.get(Delivery, fin_seed.disputed_id)).state == "ENTREGUE"


@pytest.mark.asyncio
async def test_idempotent(
    session_factory: async_sessionmaker[AsyncSession], fin_seed: FinSeed
) -> None:
    ctx = {"session_factory": session_factory}
    assert await finalize_deliveries(ctx) == 1
    # Second run finalises nothing new.
    assert await finalize_deliveries(ctx) == 0
