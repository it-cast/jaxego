"""Appeal SLA enforcement job (REQ-045 / D-05 / LOW-1). Aware-UTC, idempotent (TD-010).

`enforce_appeal_sla`: every appeal that is UNDECIDED (`decision IS NULL`), past its
`sla_due_at`, and not yet auto-reverted (`reverted_at IS NULL`) → revert the subject to
`active` (audited transition) + emit an ALERT (structlog warning + count). Idempotent:
once reverted, `reverted_at` is set, so a re-run does not touch it again; an appeal
decided in time is never reverted.

A failure on one appeal never derails the sweep (best-effort per row).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select

from app.db.mixins import ensure_aware_utc
from app.suspensions.models import SuspensionAppeal
from app.suspensions.service import _revert

logger = structlog.get_logger("workers.appeals")


async def enforce_appeal_sla(ctx: dict[str, Any]) -> int:
    """Auto-revert subjects of undecided, past-due appeals (+ alert). Returns count."""
    started = datetime.now(UTC)
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        appeals = (
            (
                await session.execute(
                    select(SuspensionAppeal).where(
                        SuspensionAppeal.decision.is_(None),
                        SuspensionAppeal.reverted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        for appeal in appeals:
            if ensure_aware_utc(appeal.sla_due_at) > started:
                continue  # not yet due — leave it
            try:
                await _revert(
                    session,
                    appeal=appeal,
                    actor_id=None,  # system actor (the job)
                    action_suffix="appeal_sla_reverted",
                )
                appeal.reverted_at = datetime.now(UTC)
                count += 1
                # ALERT: a suspension was auto-lifted because the SLA lapsed (D-05).
                logger.warning(
                    "appeals.sla_auto_reverted",
                    appeal_id=appeal.id,
                    subject_type=appeal.subject_type,
                    subject_id=appeal.subject_id,
                    area_id=appeal.area_id,
                )
            except Exception:  # noqa: BLE001 — best-effort per row (never derail sweep)
                logger.warning("appeals.sla_revert_failed", appeal_id=appeal.id)
        await session.commit()
    logger.info(
        "appeals.enforce_appeal_sla",
        reverted=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count
