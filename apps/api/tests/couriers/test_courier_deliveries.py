"""Courier-facing delivery reads (F1.0 / MR-1).

Validates: the assigned courier reads their own active/detail/list; another
courier gets 404 (IDOR — TH-03); and the serializer hides destination PII until
pickup (RN-013). In-memory SQLite (Layer 2) — no network.
"""

from __future__ import annotations

import pytest
from app.areas.models import Area
from app.auth.models import User
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.couriers.models import Courier
from app.couriers.router import _courier_delivery_out
from app.deliveries.models import Delivery, Recipient
from app.deliveries.service import (
    get_courier_active_delivery,
    get_courier_delivery,
    list_courier_deliveries,
)
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.asyncio


async def _courier(s: AsyncSession, area_id: int, email: str, cpf: str) -> Courier:
    user = User(
        email=email,
        name="Entregador",
        phone="+5522999990000",
        password_hash=hash_password("correct-horse-staple-10"),
        platform_role="user",
    )
    s.add(user)
    await s.flush()
    courier = Courier(
        area_id=area_id,
        user_id=user.id,
        cpf=cpf,
        full_name="Entregador",
        phone_e164="+5522999990000",
        email=email,
        kyc_level="completa",
        status="active",
        vehicle_type="moto",
        vehicle_plate="ABC1D23",
    )
    s.add(courier)
    await s.flush()
    return courier


async def _delivery(
    s: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    nbhd_id: int,
    recipient_id: int,
    courier_id: int | None,
    state: str,
    token: str,
) -> Delivery:
    d = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        courier_id=courier_id,
        recipient_id=recipient_id,
        state=state,
        dispatch_mode="direct",
        payment_method="direct",
        proof_method="photo",
        pickup_address="Rua das Flores, 123",
        pickup_neighborhood="Centro",
        dropoff_address="Rua Secreta, 999",
        dropoff_number="999",
        dropoff_complement="ap 2",
        dropoff_neighborhood_id=nbhd_id,
        distance_m=2800,
        estimate_min_cents=1000,
        estimate_max_cents=1000,
        fee_cents=0,
        items_quantity=1,
        public_token=token,
        origin="manual",
    )
    s.add(d)
    await s.flush()
    return d


async def _setup(s: AsyncSession):
    area = Area(codename="padua", name="Pádua", config={})
    s.add(area)
    await s.flush()
    nbhd = Neighborhood(area_id=area.id, name="Vila Nova", is_informal=False)
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
    recipient = Recipient(
        area_id=area.id,
        name="Maria Silva",
        phone_e164="+5522988887777",
        deliveries_count=0,
        refusals_count=0,
    )
    s.add_all([nbhd, merchant, recipient])
    await s.flush()
    courier_a = await _courier(s, area.id, "a@example.com", "39053344705")
    courier_b = await _courier(s, area.id, "b@example.com", "11144477735")
    return area, nbhd, merchant, recipient, courier_a, courier_b


async def test_active_and_detail_scoped_to_courier(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, nbhd, merchant, recipient, a, b = await _setup(s)
        active = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            recipient_id=recipient.id,
            courier_id=a.id,
            state="ACEITA",
            token="T" * 26,
        )
        await s.commit()

        got = await get_courier_active_delivery(s, courier_id=a.id)
        assert got is not None and got[0].id == active.id

        detail, _ = await get_courier_delivery(s, courier_id=a.id, delivery_id=active.id)
        assert detail.id == active.id

        # IDOR: courier B cannot read A's delivery → 404.
        with pytest.raises(NotFoundError):
            await get_courier_delivery(s, courier_id=b.id, delivery_id=active.id)

        # B has no active delivery.
        assert await get_courier_active_delivery(s, courier_id=b.id) is None


async def test_list_only_own_deliveries(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, nbhd, merchant, recipient, a, b = await _setup(s)
        for i, st in enumerate(["ACEITA", "ENTREGUE", "FINALIZADA"]):
            await _delivery(
                s,
                area_id=area.id,
                merchant_id=merchant.id,
                nbhd_id=nbhd.id,
                recipient_id=recipient.id,
                courier_id=a.id,
                state=st,
                token=f"A{i:025d}",
            )
        await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            recipient_id=recipient.id,
            courier_id=b.id,
            state="ACEITA",
            token=f"B{0:025d}",
        )
        await s.commit()

        page = await list_courier_deliveries(s, courier_id=a.id)
        assert page.total == 3
        page_b = await list_courier_deliveries(s, courier_id=b.id)
        assert page_b.total == 1


async def test_pii_hidden_before_pickup_revealed_after(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as s:
        area, nbhd, merchant, recipient, a, _ = await _setup(s)
        before = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            recipient_id=recipient.id,
            courier_id=a.id,
            state="ACEITA",
            token="C" * 26,
        )
        after = await _delivery(
            s,
            area_id=area.id,
            merchant_id=merchant.id,
            nbhd_id=nbhd.id,
            recipient_id=recipient.id,
            courier_id=a.id,
            state="COLETADA",
            token="D" * 26,
        )
        await s.commit()

        out_before = _courier_delivery_out(before, recipient)
        assert out_before.dropoff_address is None
        assert out_before.recipient_name is None
        # neighborhood + distance always available (it's the offer-level info)
        assert out_before.dropoff_neighborhood_id == nbhd.id

        out_after = _courier_delivery_out(after, recipient)
        assert out_after.dropoff_address == "Rua Secreta, 999"
        assert out_after.recipient_name == "Maria Silva"
        assert out_after.recipient_phone_masked is not None
