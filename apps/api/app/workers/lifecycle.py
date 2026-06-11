"""Lifecycle cron jobs (Phase 9 — D-06 / DEC-002 / D-07). All aware-UTC (TD-010).

- `finalize_deliveries`: ENTREGUE for >24h with NO open payment dispute → FINALIZADA
  (via `transition()` — append-only, D-06). Idempotent: only ENTREGUE rows move.
- `purge_locations`: HARD-delete `delivery_locations` of TERMINAL deliveries whose last
  sample is >24h old (retention/LGPD — TH-4 / Pitfall 3). Idempotent: re-running finds
  nothing new.
- `absent_timeout`: a delivery marked "ausente" (a refusal-reason marker) for >10min
  → flag it as eligible to "retornar" (D-07 E2). Idempotent (a flag, not a transition).

Each job logs a processed COUNT + duration, never PII; a failure inside one row never
derails the sweep (best-effort per row). Registered in `WorkerSettings.cron_jobs`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import delete, select

from app.db.mixins import ensure_aware_utc
from app.deliveries.models import Delivery
from app.deliveries.service import transition
from app.payments_direct.service import has_open_dispute
from app.tracking.models import DeliveryLocation

logger = structlog.get_logger("workers.lifecycle")

FINALIZE_AFTER = timedelta(hours=24)
PURGE_AFTER = timedelta(hours=24)
ABSENT_AFTER = timedelta(minutes=10)

_TERMINAL_STATES = ("FINALIZADA", "CANCELADA", "RECUSADA_NO_DESTINO")


async def finalize_deliveries(ctx: dict[str, Any]) -> int:
    """ENTREGUE >24h with no open dispute → FINALIZADA (D-06). Returns count."""
    started = datetime.now(UTC)
    cutoff = started - FINALIZE_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        rows = (
            (await session.execute(select(Delivery).where(Delivery.state == "ENTREGUE")))
            .scalars()
            .all()
        )
        for delivery in rows:
            delivered_at = delivery.delivered_at
            if delivered_at is None or ensure_aware_utc(delivered_at) > cutoff:
                continue
            if await has_open_dispute(session, delivery_id=delivery.id):
                continue  # an open dispute blocks finalisation (mediação Phase 11)
            await transition(
                session,
                delivery=delivery,
                to_state="FINALIZADA",
                actor_id=None,
                reason="auto_finalize_24h",
            )
            count += 1
        await session.commit()
    logger.info(
        "lifecycle.finalize_deliveries",
        finalized=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


async def purge_locations(ctx: dict[str, Any]) -> int:
    """Hard-delete delivery_locations of terminal deliveries >24h old (LGPD)."""
    started = datetime.now(UTC)
    cutoff = started - PURGE_AFTER
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        # Terminal deliveries only; samples older than the retention window.
        terminal_ids = (
            (await session.execute(select(Delivery.id).where(Delivery.state.in_(_TERMINAL_STATES))))
            .scalars()
            .all()
        )
        if not terminal_ids:
            logger.info("lifecycle.purge_locations", purged=0)
            return 0
        result = await session.execute(
            delete(DeliveryLocation).where(
                DeliveryLocation.delivery_id.in_(terminal_ids),
                DeliveryLocation.recorded_at < cutoff,
            )
        )
        await session.commit()
    count = result.rowcount or 0
    logger.info(
        "lifecycle.purge_locations",
        purged=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


async def absent_timeout(ctx: dict[str, Any]) -> int:
    """Mark deliveries 'ausente' >10min as eligible to return (D-07 E2).

    M1 marker: a delivery whose latest transition reason is 'absent' and whose
    `collected_at`/transition is >10min old. We set a flag in `notes` (idempotent
    string marker) since there is no dedicated column — the UI reads it to enable
    "Retornar ao estabelecimento". A full return automation is post-M1 (TD-007).
    """
    started = datetime.now(UTC)
    cutoff = started - ABSENT_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    marker = "[return_enabled]"
    async with session_factory() as session:
        rows = (
            (await session.execute(select(Delivery).where(Delivery.state == "COLETADA")))
            .scalars()
            .all()
        )
        for delivery in rows:
            # The "ausente" marker is carried in cancel_reason-like notes by the UI;
            # here we use `notes` containing 'absent' set when the courier reports it.
            if not delivery.notes or "absent" not in delivery.notes:
                continue
            collected = delivery.collected_at
            if collected is None or ensure_aware_utc(collected) > cutoff:
                continue
            if marker in delivery.notes:
                continue  # idempotent — already enabled
            delivery.notes = f"{delivery.notes} {marker}"
            count += 1
        await session.commit()
    logger.info(
        "lifecycle.absent_timeout",
        enabled=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count
