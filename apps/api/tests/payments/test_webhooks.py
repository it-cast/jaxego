"""Webhooks: log → HMAC → dedup → enqueue → 200. Idempotent; HMAC invalid → 403.

TH-E: order is mandatory; `secrets.compare_digest` (never ==); a duplicate
(tx,status) is processed once. Business error → log+enqueue+200 (never 500 — Safe2Pay
would retry forever).
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from app.payments.models import PaymentWebhookEvent
from sqlalchemy import func, select

WEBHOOK_SECRET = "test-webhook-secret"


def _sign(body: bytes) -> str:
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_already_processed_dedups(payments_seed, session_factory) -> None:
    from app.payments import repo

    async with session_factory() as s:
        first = await repo.mark_webhook_seen(s, area_id=None, transaction_id="tx_w1", status="3")
        await s.commit()
        assert first is True
    async with session_factory() as s:
        second = await repo.mark_webhook_seen(s, area_id=None, transaction_id="tx_w1", status="3")
        await s.commit()
        assert second is False  # duplicate (tx,status) → not seen-again
        n = (
            await s.execute(
                select(func.count(PaymentWebhookEvent.id)).where(
                    PaymentWebhookEvent.transaction_id == "tx_w1"
                )
            )
        ).scalar_one()
        assert n == 1


def test_verify_hmac_uses_compare_digest() -> None:
    from app.payments import webhooks_router

    body = b'{"IdTransaction":"x","Status":"3"}'
    sig = _sign(body)
    assert webhooks_router._verify_hmac(body, sig, secret=WEBHOOK_SECRET) is True
    assert webhooks_router._verify_hmac(body, "deadbeef", secret=WEBHOOK_SECRET) is False
    assert webhooks_router._verify_hmac(body, None, secret=WEBHOOK_SECRET) is False


@pytest.mark.asyncio
async def test_webhook_endpoint_dedup_one_effect(auth_payments_client) -> None:
    body = json.dumps({"IdTransaction": "tx_dup", "Status": "3"}).encode()
    headers = {"x-safe2pay-signature": _sign(body), "content-type": "application/json"}
    r1 = await auth_payments_client.post(
        "/v1/payments/webhooks/safe2pay", content=body, headers=headers
    )
    r2 = await auth_payments_client.post(
        "/v1/payments/webhooks/safe2pay", content=body, headers=headers
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get("idempotent") is True


@pytest.mark.asyncio
async def test_webhook_bad_signature_403(auth_payments_client) -> None:
    body = json.dumps({"IdTransaction": "tx_bad", "Status": "3"}).encode()
    headers = {"x-safe2pay-signature": "deadbeef", "content-type": "application/json"}
    r = await auth_payments_client.post(
        "/v1/payments/webhooks/safe2pay", content=body, headers=headers
    )
    assert r.status_code == 403
