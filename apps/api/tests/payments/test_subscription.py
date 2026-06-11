"""Subscription activation (card tokenized / PIX) + recurring cron idempotency.

REQ-010 / SAAS-BILLING §5-7. Sandbox charges raw → production tokenizes→charges with
token; the recurring cron is idempotent (only `situacao=0` open charges).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.merchants.models import MerchantSubscription


@pytest.mark.asyncio
async def test_activate_card_sets_active_and_token(
    payments_seed, payment_stub, session_factory, crypto_keys
) -> None:
    from app.payments import subscriptions

    async with session_factory() as s:
        sub = await subscriptions.activate_card(
            s,
            subscription_id=payments_seed.subscription_id,
            plan_id=payments_seed.pro_plan_id,
            cycle="mensal",
            raw_card_token="tok_real",
            customer_name="Loja",
            customer_document="12345678000190",
            customer_email="loja@example.com",
            payment=payment_stub,
        )
        await s.commit()
        assert sub.billing_status == "active"
        assert sub.payment_method == "card"
        # The stored token is AES-encrypted at rest.
        assert sub.safe2pay_token is not None
        assert sub.safe2pay_token != "tok_real"


@pytest.mark.asyncio
async def test_activate_pix_pending_until_webhook(
    payments_seed, payment_stub, session_factory
) -> None:
    from app.payments import subscriptions

    async with session_factory() as s:
        sub = await subscriptions.activate_pix(
            s,
            subscription_id=payments_seed.subscription_id,
            plan_id=payments_seed.pro_plan_id,
            cycle="mensal",
            customer_name="Loja",
            customer_document="12345678000190",
            customer_email="loja@example.com",
            payment=payment_stub,
        )
        await s.commit()
        # PIX does NOT activate immediately — waits for webhook APROVADA.
        assert sub.billing_status != "active"
        assert sub.pix_qr_code is not None
        assert sub.pix_autorizacao_id is not None


@pytest.mark.asyncio
async def test_recurring_charge_idempotent(
    payments_seed, payment_stub, session_factory, crypto_keys
) -> None:
    from app.payments import subscriptions

    # Make the subscription a card-active subscription due today.
    async with session_factory() as s:
        sub = await s.get(MerchantSubscription, payments_seed.subscription_id)
        sub.billing_status = "active"
        sub.payment_method = "card"
        sub.cycle = "mensal"
        sub.amount_cents = 9990
        sub.due_at = datetime.now(UTC) - timedelta(days=1)
        from app.payments.crypto import encrypt_token

        sub.safe2pay_token = encrypt_token("tok_real")
        await s.commit()

    charged_first = await subscriptions.charge_due_subscriptions(session_factory, payment_stub)
    charged_second = await subscriptions.charge_due_subscriptions(session_factory, payment_stub)
    assert charged_first == 1
    # After charging, due_at moved forward → no second charge same run.
    assert charged_second == 0
