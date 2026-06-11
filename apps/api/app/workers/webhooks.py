"""arq jobs for the public API (Phase 12) — idempotency purge + webhook delivery.

- `purge_idempotency_keys` (T-05): sweep expired `api_idempotency_keys` (aware-UTC,
  idempotent; a re-run on an already-empty window is a 0-row no-op).
- `deliver_due_webhooks` (T-09): pick up `pending` webhook deliveries whose
  `next_retry_at` has arrived and run ONE attempt each. The exact backoff lives in
  `webhooks.delivery.apply_attempt_result`; this sweep just drives it. A failure in
  one row never derails the sweep (each is committed independently).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger("workers.webhooks")


async def purge_idempotency_keys(ctx: dict[str, Any]) -> int:
    """Delete expired idempotency snapshots (T-05). Returns the rows purged."""
    from app.api_keys import repo

    session_factory = ctx["session_factory"]
    now = datetime.now(UTC)  # AWARE — TD-010
    async with session_factory() as session:
        count = await repo.purge_expired_idempotency(session, now=now)
        await session.commit()
    logger.info("webhooks.idempotency_purged", count=count)
    return count


async def deliver_due_webhooks(ctx: dict[str, Any]) -> int:
    """Run one attempt for each pending webhook delivery that is due (T-09).

    Returns the number of attempts made. The exact 8× backoff is applied per row by
    `apply_attempt_result`; a `pending` row keeps its future `next_retry_at` and is
    re-swept when it comes due. A 2xx → `delivered`; the 8th failure → `failed`+alert.
    """
    from app.webhooks import repo
    from app.webhooks.delivery import attempt_delivery

    session_factory = ctx["session_factory"]
    now = datetime.now(UTC)  # AWARE — TD-010
    attempts = 0
    async with session_factory() as session:
        due = await repo.due_deliveries(session, now=now)
        for row in due:
            try:
                await attempt_delivery(session, webhook_delivery_id=row.id, now=now)
                await session.commit()
                attempts += 1
            except Exception:  # noqa: BLE001 — one bad row never derails the sweep
                await session.rollback()
                logger.warning("webhooks.delivery_attempt_error", webhook_delivery_id=row.id)
    if attempts:
        logger.info("webhooks.deliveries_attempted", count=attempts)
    return attempts
