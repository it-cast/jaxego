"""Direct payment confirmation (RN-026 / D-05): cash/pix records; não recebi → dispute.

`confirm_direct_payment` records the confirmation; "not_received" additionally opens a
PaymentDispute (status open). The delivery stays ENTREGUE (the money outcome does not
change the state). `has_open_dispute` reflects the open dispute (it blocks the 24h
finalisation job in T-07).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.payments_direct.models import DirectPaymentConfirmation, PaymentDispute
from app.payments_direct.service import confirm_direct_payment, has_open_dispute
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class PaySeed:
    delivery_id: int
    courier_id: int


@pytest_asyncio.fixture
async def pay_seed(session_factory: async_sessionmaker[AsyncSession]) -> PaySeed:
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()
        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()
        user = User(
            email="c@example.com",
            name="C",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add(user)
        await s.flush()
        courier = Courier(
            area_id=area.id,
            user_id=user.id,
            cpf="39053344705",
            full_name="C",
            phone_e164="+5522999990000",
            email="c@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
            max_concurrent=2,
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
        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=courier.id,
            state="ENTREGUE",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="a",
            dropoff_address="b",
            dropoff_neighborhood_id=nbhd.id,
            fee_cents=0,
            items_quantity=1,
            public_token="PAYTOKEN00000000000000000A",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        await s.commit()
        return PaySeed(delivery_id=delivery.id, courier_id=courier.id)


@pytest.mark.asyncio
async def test_cash_records_confirmation_no_dispute(
    session_factory: async_sessionmaker[AsyncSession], pay_seed: PaySeed
) -> None:
    async with session_factory() as s:
        delivery = await s.get(Delivery, pay_seed.delivery_id)
        conf, dispute = await confirm_direct_payment(
            s, delivery=delivery, courier_id=pay_seed.courier_id, outcome="cash", amount_cents=2500
        )
        await s.commit()
        assert dispute is None
        assert conf.outcome == "cash"
        assert conf.amount_cents == 2500
        assert await has_open_dispute(s, delivery_id=pay_seed.delivery_id) is False
        # Delivery stays ENTREGUE (money does not change state).
        assert (await s.get(Delivery, pay_seed.delivery_id)).state == "ENTREGUE"


@pytest.mark.asyncio
async def test_not_received_opens_dispute(
    session_factory: async_sessionmaker[AsyncSession], pay_seed: PaySeed
) -> None:
    async with session_factory() as s:
        delivery = await s.get(Delivery, pay_seed.delivery_id)
        conf, dispute = await confirm_direct_payment(
            s,
            delivery=delivery,
            courier_id=pay_seed.courier_id,
            outcome="not_received",
            amount_cents=None,
        )
        await s.commit()
        assert dispute is not None
        assert dispute.status == "open"
        assert conf.amount_cents is None
        assert await has_open_dispute(s, delivery_id=pay_seed.delivery_id) is True
        # Still ENTREGUE — não recebi não trava a conclusão.
        assert (await s.get(Delivery, pay_seed.delivery_id)).state == "ENTREGUE"


@pytest.mark.asyncio
async def test_persistence(
    session_factory: async_sessionmaker[AsyncSession], pay_seed: PaySeed
) -> None:
    async with session_factory() as s:
        delivery = await s.get(Delivery, pay_seed.delivery_id)
        await confirm_direct_payment(
            s, delivery=delivery, courier_id=pay_seed.courier_id, outcome="pix", amount_cents=1500
        )
        await s.commit()
    async with session_factory() as s:
        conf = (
            await s.execute(
                select(DirectPaymentConfirmation).where(
                    DirectPaymentConfirmation.delivery_id == pay_seed.delivery_id
                )
            )
        ).scalar_one()
        assert conf.outcome == "pix"
        disputes = (
            (
                await s.execute(
                    select(PaymentDispute).where(PaymentDispute.delivery_id == pay_seed.delivery_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(disputes) == 0
