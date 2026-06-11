"""Plan change: upgrade pro-rata (cents) now; downgrade scheduled (RN-029).

REQ-011. Upgrade charges the pro-rated difference for the remaining cycle days,
computed in integer cents. Downgrade does NOT charge now — it schedules for cycle end.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


def test_prorata_cents_half_cycle() -> None:
    from app.payments.subscriptions import prorata_upgrade_cents

    # current 5000c/mo, target 10000c/mo, 15 of 30 days remaining → diff 5000 * 15/30.
    now = datetime(2026, 6, 16, tzinfo=UTC)
    cycle_end = datetime(2026, 7, 1, tzinfo=UTC)
    cents = prorata_upgrade_cents(
        current_cents=5000, target_cents=10000, now=now, cycle_end=cycle_end, cycle_days=30
    )
    assert cents == 2500  # (10000-5000) * 15/30


def test_prorata_never_negative() -> None:
    from app.payments.subscriptions import prorata_upgrade_cents

    now = datetime(2026, 6, 16, tzinfo=UTC)
    cycle_end = datetime(2026, 7, 1, tzinfo=UTC)
    # Downgrade (target < current) → pro-rata upgrade charge is 0.
    cents = prorata_upgrade_cents(
        current_cents=10000, target_cents=5000, now=now, cycle_end=cycle_end, cycle_days=30
    )
    assert cents == 0


@pytest.mark.asyncio
async def test_upgrade_charges_now(payments_seed, payment_stub, session_factory) -> None:
    from app.merchants.models import MerchantSubscription
    from app.payments import subscriptions

    async with session_factory() as s:
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        sub.billing_status = "active"
        sub.payment_method = "card"
        sub.plan_id = payments_seed.free_plan_id
        sub.amount_cents = 0
        sub.cycle = "mensal"
        sub.due_at = datetime.now(UTC) + timedelta(days=15)
        from app.payments.crypto import encrypt_token

        sub.safe2pay_token = encrypt_token("tok_real")
        await s.commit()

        result = await subscriptions.change_plan(
            s,
            subscription_id=payments_seed.subscription_id,
            target_plan_id=payments_seed.pro_plan_id,
            payment=payment_stub,
        )
        await s.commit()
        assert result["kind"] == "upgrade"
        assert result["charged_cents"] >= 0
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        assert sub.plan_id == payments_seed.pro_plan_id  # upgrade is immediate


@pytest.mark.asyncio
async def test_downgrade_scheduled(payments_seed, payment_stub, session_factory) -> None:
    from app.merchants.models import MerchantSubscription
    from app.payments import subscriptions

    async with session_factory() as s:
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        sub.billing_status = "active"
        sub.payment_method = "card"
        sub.plan_id = payments_seed.pro_plan_id
        sub.amount_cents = 9990
        sub.cycle = "mensal"
        sub.due_at = datetime.now(UTC) + timedelta(days=15)
        await s.commit()

        result = await subscriptions.change_plan(
            s,
            subscription_id=payments_seed.subscription_id,
            target_plan_id=payments_seed.free_plan_id,
            payment=payment_stub,
        )
        await s.commit()
        assert result["kind"] == "downgrade"
        assert result["charged_cents"] == 0
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        # Plan NOT changed yet — scheduled for cycle end.
        assert sub.plan_id == payments_seed.pro_plan_id
        assert sub.scheduled_plan_id == payments_seed.free_plan_id
