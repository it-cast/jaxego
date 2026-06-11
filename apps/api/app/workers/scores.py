"""Daily score snapshot job (REQ-020 / ADR-013). Aware-UTC, idempotent (TD-010).

`snapshot_scores` builds ONE snapshot per active courier per day. Idempotent: re-running
on the same day updates the existing (courier, day) row instead of inserting a duplicate
(the UNIQUE (courier_id, snapshot_date) + the service UPSERT guarantee 1/dia/courier).

It reads only DERIVED signals (no PII into the aggregate — TH-07) and writes nothing to
dispatch/ranking (ADR-013). A failure on one courier never derails the sweep.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select

from app.couriers.models import Courier
from app.scores.service import build_snapshot
from app.scores.signals import compute_signals

logger = structlog.get_logger("workers.scores")


async def snapshot_scores(ctx: dict[str, Any]) -> int:
    """Build today's score snapshot for every active courier (idempotent). Returns count."""
    started = datetime.now(UTC)
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        couriers = (
            (
                await session.execute(
                    select(Courier).where(
                        Courier.status == "active",
                        Courier.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        for courier in couriers:
            try:
                signals = await compute_signals(session, courier_id=courier.id)
                await build_snapshot(
                    session,
                    courier_id=courier.id,
                    area_id=courier.area_id,
                    signals=signals,
                )
                count += 1
            except Exception:  # noqa: BLE001 — best-effort per row (never derail sweep)
                logger.warning("scores.snapshot_failed", courier_id=courier.id)
        await session.commit()
    logger.info(
        "scores.snapshot_scores",
        snapshotted=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count
