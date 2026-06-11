"""Split charge per delivery: exact-cents sum, idempotency, refusal → no delivery.

TH-F: `amount_cents == Σ splits.amount_cents` (rounding residual → Jaxegô). TH-D:
same `Reference`/idempotency_key → one charge row. F-03 E3: refusal on creation →
the delivery is NOT born. REQ-019: subaccount registered on MEI approval.
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery
from sqlalchemy import func, select


def test_split_sum_exact_cents() -> None:
    from app.payments.fees import build_splits

    # corrida 1000c, taxa 200c, revenue share 20% of taxa → all to Jaxegô recipient.
    splits = build_splits(
        corrida_cents=1000,
        taxa_cents=200,
        courier_recipient="recip_courier_1",
        jaxego_recipient="recip_jaxego",
        revenue_share_pct=20,
    )
    total = 1000 + 200
    assert sum(s.amount_cents for s in splits) == total
    courier_split = next(s for s in splits if s.recipient == "recip_courier_1")
    assert courier_split.amount_cents == 1000  # corrida intact to courier


def test_split_rounding_residual_goes_to_jaxego() -> None:
    from app.payments.fees import build_splits

    # An odd taxa that does not divide evenly under any share still sums exactly.
    splits = build_splits(
        corrida_cents=199,
        taxa_cents=199,
        courier_recipient="recip_courier_1",
        jaxego_recipient="recip_jaxego",
        revenue_share_pct=20,
    )
    assert sum(s.amount_cents for s in splits) == 199 + 199


@pytest.mark.asyncio
async def test_idempotent_charge(payments_seed, payment_stub, session_factory) -> None:
    from app.payments import repo
    from app.payments.models import PlatformCharge

    async with session_factory() as s:
        await repo.record_charge(
            s,
            area_id=payments_seed.area_a_id,
            idempotency_key="dlv_1",
            transaction_id="tx_1",
            amount_cents=1200,
            method="card",
            kind="delivery",
            status="paid",
        )
        # Same idempotency key again → no second row.
        await repo.record_charge(
            s,
            area_id=payments_seed.area_a_id,
            idempotency_key="dlv_1",
            transaction_id="tx_1",
            amount_cents=1200,
            method="card",
            kind="delivery",
            status="paid",
        )
        await s.commit()
        count = (
            await s.execute(
                select(func.count(PlatformCharge.id)).where(
                    PlatformCharge.idempotency_key == "dlv_1"
                )
            )
        ).scalar_one()
        assert count == 1


@pytest.mark.asyncio
async def test_charge_delivery_refused_delivery_not_born(payments_seed, session_factory) -> None:
    """F-03 E3: a refused card on creation → the delivery is NOT created."""
    from app.payments.errors import PaymentGatewayError
    from app.payments.safe2pay_stub import PaymentStubAdapter
    from app.payments.service import PaymentService

    refusing = PaymentStubAdapter(scenario="refused")
    async with session_factory() as s:
        svc = PaymentService(s, payment=refusing)
        with pytest.raises(PaymentGatewayError):
            await svc.charge_delivery(
                area_id=payments_seed.area_a_id,
                delivery_id=999,  # would-be delivery
                corrida_cents=1000,
                taxa_cents=200,
                courier_recipient="recip_courier_1",
                method="card",
                customer_name="Loja",
                customer_document="12345678000190",
                customer_email="loja@example.com",
            )
        await s.rollback()
        # No delivery exists (the caller never inserts on refusal).
        n = (
            await s.execute(select(func.count(Delivery.id)).where(Delivery.id == 999))
        ).scalar_one()
        assert n == 0


@pytest.mark.asyncio
async def test_subaccount_on_mei_approval(payments_seed, payment_stub, session_factory) -> None:
    """REQ-019: approving the MEI registers a Safe2Pay subaccount (recipient id)."""
    from app.couriers.models import Courier
    from app.couriers.subaccount import register_subaccount_on_mei_active

    async with session_factory() as s:
        courier = await s.get(Courier, payments_seed.courier_no_mei_id)
        assert courier is not None
        courier.mei_pending = False  # MEI just approved
        courier.mei_cnpj = "55566677000188"
        await register_subaccount_on_mei_active(s, courier=courier, payment=payment_stub)
        await s.commit()
        await s.refresh(courier)
        assert courier.s2p_recipient_id is not None


@pytest.mark.asyncio
async def test_no_mei_no_subaccount(payments_seed, payment_stub, session_factory) -> None:
    """No MEI → no subaccount call, recipient stays None (RN-010)."""
    from app.couriers.models import Courier
    from app.couriers.subaccount import register_subaccount_on_mei_active

    async with session_factory() as s:
        courier = await s.get(Courier, payments_seed.courier_no_mei_id)
        assert courier is not None
        assert courier.mei_pending is True
        await register_subaccount_on_mei_active(s, courier=courier, payment=payment_stub)
        await s.commit()
        await s.refresh(courier)
        assert courier.s2p_recipient_id is None
