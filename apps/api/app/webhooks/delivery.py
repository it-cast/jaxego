"""Webhook delivery with EXACT 8× backoff (T-09 / LOW-1 / TH-10).

The backoff is the ADR-010 schedule, EXACTLY: the i-th attempt (1-indexed) that
fails schedules the next attempt `BACKOFF[i]` seconds later. The 1st attempt fires
immediately (the enqueue sets `next_retry_at=now`), so the OFFSETS between attempts
are `[30, 120, 600, 3600, 14400, 43200, 86400]` after attempts 1..7; the 8th
failure is terminal → `failed` + alert (no 9th attempt).

`compute_next_retry(attempts)` and `apply_attempt_result(...)` are PURE and
clock-injectable so the test proves the 8 instants with a controlled clock (no
sleeps). The arq job (`deliver_webhook_task`) wires them to httpx + the DB and
re-enqueues itself via `_defer_by` for the next interval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger("webhooks.delivery")

# ADR-010 exact backoff: seconds AFTER a failed attempt before the next one.
# Indexed 1..8 by the attempt number that just failed; attempt 1 fired at enqueue
# (offset 0). BACKOFF_AFTER[k] = wait after the k-th failed attempt.
# Attempt 1 fails → wait 30s; … attempt 7 fails → wait 86400s; attempt 8 fails → terminal.
BACKOFF_AFTER_SECONDS = (30, 120, 600, 3600, 14400, 43200, 86400)
MAX_ATTEMPTS = 8

# The canonical cumulative offsets from the first attempt (for the test assertion):
# attempt 1 @ 0s, 2 @ 30s, 3 @ 150s, 4 @ 750s, 5 @ 4350s, 6 @ 18750s, 7 @ 61950s, 8 @ 148350s.
CUMULATIVE_OFFSETS_SECONDS = (0, 30, 150, 750, 4350, 18750, 61950, 148350)


def compute_next_retry(*, failed_attempt: int, now: datetime) -> datetime | None:
    """Instant of the next attempt after `failed_attempt` failed, or None if terminal.

    `failed_attempt` is 1-indexed. Returns `now + BACKOFF_AFTER_SECONDS[failed_attempt-1]`
    for attempts 1..7; None after the 8th (terminal → `failed`).
    """
    if failed_attempt >= MAX_ATTEMPTS:
        return None
    wait = BACKOFF_AFTER_SECONDS[failed_attempt - 1]
    return now + timedelta(seconds=wait)


@dataclass
class AttemptOutcome:
    """The result of recording one delivery attempt against a WebhookDelivery row."""

    status: str  # "delivered" | "pending" | "failed"
    next_retry_at: datetime | None
    terminal: bool


def apply_attempt_result(
    delivery_row,
    *,
    status_code: int | None,
    now: datetime,
) -> AttemptOutcome:
    """Mutate `delivery_row` for one attempt result (PURE w.r.t. the clock).

    - 2xx → `delivered` (terminal, success).
    - non-2xx / no response, attempt < 8 → `pending`, schedule the next retry.
    - non-2xx / no response, attempt == 8 → `failed` (terminal) + alert.
    """
    delivery_row.attempts += 1
    delivery_row.last_status_code = status_code

    if status_code is not None and 200 <= status_code < 300:
        delivery_row.status = "delivered"
        delivery_row.delivered_at = now
        delivery_row.next_retry_at = None
        return AttemptOutcome(status="delivered", next_retry_at=None, terminal=True)

    # A 4xx other than 429 is a PERMANENT failure — no retry (integration contract §2):
    # the receiver rejected the payload (bad config/auth), retrying won't help.
    if status_code is not None and 400 <= status_code < 500 and status_code != 429:
        delivery_row.status = "failed"
        delivery_row.next_retry_at = None
        logger.error(
            "webhook.delivery_failed_permanent",
            area_id=delivery_row.area_id,
            webhook_delivery_id=delivery_row.id,
            event_type=delivery_row.event_type,
            attempts=delivery_row.attempts,
            last_status_code=status_code,
        )
        return AttemptOutcome(status="failed", next_retry_at=None, terminal=True)

    next_retry = compute_next_retry(failed_attempt=delivery_row.attempts, now=now)
    if next_retry is None:
        delivery_row.status = "failed"
        delivery_row.next_retry_at = None
        # Observability alert — repeated receiver failure after the full backoff (TH-10).
        logger.error(
            "webhook.delivery_failed",
            area_id=delivery_row.area_id,
            webhook_delivery_id=delivery_row.id,
            event_type=delivery_row.event_type,
            attempts=delivery_row.attempts,
            last_status_code=status_code,
        )
        return AttemptOutcome(status="failed", next_retry_at=None, terminal=True)

    delivery_row.status = "pending"
    delivery_row.next_retry_at = next_retry
    return AttemptOutcome(status="pending", next_retry_at=next_retry, terminal=False)


async def _post_webhook(*, url: str, headers: dict[str, str], body: bytes) -> int | None:
    """POST the signed payload; return the status code, or None on a transport error."""
    from app.integrations.http import build_client

    try:
        async with build_client() as client:
            resp = await client.post(url, content=body, headers=headers)
            return resp.status_code
    except Exception:  # noqa: BLE001 — any transport error is a failed attempt (retry)
        logger.warning("webhook.transport_error", url_host=url.split("/")[2] if "//" in url else "")
        return None


async def attempt_delivery(session, *, webhook_delivery_id: int, now: datetime) -> AttemptOutcome:
    """Run ONE delivery attempt for a WebhookDelivery row (signs, POSTs, records).

    Re-validates the URL anti-SSRF before connecting (defence in depth — TH-05),
    signs the stored payload, POSTs it, and applies the attempt result. Returns the
    outcome so the job can decide whether to re-enqueue.
    """
    import time

    from app.webhooks import repo
    from app.webhooks.signing import sign_payload
    from app.webhooks.ssrf import WebhookUrlInvalidError, assert_safe_webhook_url

    row = await repo.get_delivery(session, delivery_pk=webhook_delivery_id)
    if row is None or row.status != "pending":
        return AttemptOutcome(
            status=(row.status if row else "missing"), next_retry_at=None, terminal=True
        )

    from app.webhooks.models import WebhookEndpoint

    endpoint = await session.get(WebhookEndpoint, row.endpoint_id)
    if endpoint is None or not endpoint.enabled:
        # No endpoint to deliver to — record a failed attempt (will retry/expire).
        return apply_attempt_result(row, status_code=None, now=now)

    body = row.payload.encode("utf-8")
    timestamp = int(time.time())
    signature = sign_payload(endpoint.secret, timestamp=timestamp, raw_body=body)
    headers = {
        "Content-Type": "application/json",
        "X-Jaxego-Signature": signature,
        "X-Jaxego-Event-Id": row.event_id,
    }

    status_code: int | None
    try:
        assert_safe_webhook_url(endpoint.url)
        status_code = await _post_webhook(url=endpoint.url, headers=headers, body=body)
    except WebhookUrlInvalidError:
        # URL became unsafe (e.g. DNS rebinding) — treat as a failed attempt.
        status_code = None

    return apply_attempt_result(row, status_code=status_code, now=now)
