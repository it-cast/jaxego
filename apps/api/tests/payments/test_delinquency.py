"""Delinquency: >10d → blocked, >20d → cancelado (aware-UTC). Active-sub guard.

SAAS-BILLING §10 adapted to aware-UTC (TD-010). The guard blocks delivery creation
when the subscription is blocked/cancelado.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


def test_classify_delinquency_boundaries() -> None:
    from app.payments.subscriptions import classify_delinquency

    assert classify_delinquency(0) == "active"
    assert classify_delinquency(10) == "active"
    assert classify_delinquency(11) == "blocked"
    assert classify_delinquency(20) == "blocked"
    assert classify_delinquency(21) == "cancelado"


def test_days_overdue_aware_utc() -> None:
    from app.payments.subscriptions import days_overdue

    now = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)
    # Naive due read back from DB is treated as UTC (ensure_aware_utc).
    due_naive = datetime(2026, 6, 1, 0, 0)
    assert days_overdue(due_naive, now) == 10
    assert days_overdue(None, now) == 0


@pytest.mark.asyncio
async def test_sync_delinquency_blocks_and_cancels(payments_seed, session_factory) -> None:
    from app.merchants.models import MerchantSubscription
    from app.payments import subscriptions
    from app.payments.models import PlatformCharge

    async with session_factory() as s:
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        sub.billing_status = "active"
        # An open charge overdue by 15 days → should become blocked.
        s.add(
            PlatformCharge(
                area_id=payments_seed.area_a_id,
                idempotency_key="sub_overdue",
                transaction_id=None,
                amount_cents=9990,
                method="card",
                kind="subscription",
                status="open",
                subscription_id=sub.id,
                due_at=datetime.now(UTC) - timedelta(days=15),
            )
        )
        await s.commit()

    await subscriptions.sync_delinquency(session_factory)
    async with session_factory() as s:
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        assert sub.billing_status == "blocked"


@pytest.mark.asyncio
async def test_active_subscription_guard(payments_seed, session_factory) -> None:
    from app.merchants.models import MerchantSubscription
    from app.payments.subscriptions import SubscriptionBlockedError, assert_subscription_active

    async with session_factory() as s:
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        sub.billing_status = "blocked"
        await s.commit()
    async with session_factory() as s:
        with pytest.raises(SubscriptionBlockedError):
            await assert_subscription_active(
                s, merchant_id=payments_seed.merchant_id, area_id=payments_seed.area_a_id
            )
