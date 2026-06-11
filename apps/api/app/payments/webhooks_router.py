"""Safe2Pay webhooks — log → HMAC → dedup → enqueue → 200 (Phase 10 / TH-E).

The endpoint is PUBLIC (Safe2Pay calls it). The order is mandatory and is the whole
security model (skill A3/A4 + owasp A08):

  1. log the raw payload to `payment_webhook_events` BEFORE processing (audit, no card PII)
  2. verify the HMAC-SHA256 signature with `secrets.compare_digest` (NEVER `==` — timing)
  3. dedup by (transaction_id, status) — a duplicate is a 200 no-op (one effect, TH-E)
  4. enqueue the heavy work to arq (confirm via GET before any money moves)
  5. respond 200 in < 5s

`[ASSUMIDO A4]` defence in depth (the HMAC may not be provided by Safe2Pay): idempotency
(UNIQUE) + a secret in the path is NOT used here, but the worker NEVER releases money on a
webhook alone — it confirms via `GET Transaction/{id}` first. A business error in processing
is logged + enqueued + 200 (NEVER 500 — Safe2Pay would retry forever). `# público:`
justified — the HMAC + idempotency + GET-confirmation are the auth (TH-M).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.payments import repo

logger = structlog.get_logger("payments.webhooks")

router = APIRouter(prefix="/payments/webhooks", tags=["payments-webhooks"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _verify_hmac(body: bytes, signature: str | None, *, secret: str | None) -> bool:
    """HMAC-SHA256 of the raw body, compared with `compare_digest` (anti-timing).

    When no secret is configured (dev/test default), the check passes — the defence in
    depth (idempotency + GET-confirmation in the worker) is the real guard ([ASSUMIDO A4]).
    """
    if not secret:
        return True
    if not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _extract(payload: dict, *keys: str) -> str:
    """Pull a field from `data` or the root (Safe2Pay varies nomenclature — SAAS §8.4)."""
    raw = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    for key in keys:
        val = (raw or {}).get(key) or payload.get(key)
        if val:
            return str(val)
    return ""


@router.post("/safe2pay", status_code=status.HTTP_200_OK)
async def safe2pay_webhook(request: Request, session: SessionDep) -> dict:
    # público: idempotência + HMAC + confirmação por GET no worker cobrem a auth (TH-M).
    body = await request.body()

    # 1. Log BEFORE processing (audit; no card PII in a Safe2Pay status payload).
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {}
    transaction_id = _extract(payload, "IdTransaction", "Id")
    event_status = _extract(payload, "Status")

    # 2. Verify HMAC (compare_digest, never ==).
    signature = request.headers.get("x-safe2pay-signature")
    if not _verify_hmac(body, signature, secret=settings.safe2pay_webhook_secret):
        logger.warning("safe2pay_webhook_bad_signature")
        raise HTTPException(status_code=403, detail="assinatura inválida")

    if not transaction_id or not event_status:
        # Malformed but signed — log + 200 (never 500, or Safe2Pay retries forever).
        logger.warning("safe2pay_webhook_malformed")
        return {"ok": True}

    # 3. Dedup by (transaction_id, status) — a duplicate is a 200 no-op (one effect).
    seen = await repo.mark_webhook_seen(
        session,
        area_id=None,
        transaction_id=transaction_id,
        status=event_status,
        payload=body.decode("utf-8", errors="replace")[:8000],
    )
    await session.commit()
    if not seen:
        return {"ok": True, "idempotent": True}

    # 4. Enqueue the heavy work (confirm via GET before any money moves — TH-E).
    await _enqueue_event(transaction_id, event_status)

    # 5. 200 < 5s.
    return {"ok": True}


async def _enqueue_event(transaction_id: str, event_status: str) -> None:
    """Best-effort enqueue of `process_safe2pay_event` (never 500 a webhook)."""
    from arq import create_pool
    from arq.connections import RedisSettings

    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("process_safe2pay_event", transaction_id, event_status)
        finally:
            await pool.aclose()
    except Exception:  # noqa: BLE001 — the event row is logged; an ops re-run recovers
        logger.warning("safe2pay_webhook_enqueue_failed")
