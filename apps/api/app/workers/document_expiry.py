"""Document expiry + 48h escalation jobs (T-09) — aware-UTC (TD-010).

Two batch jobs, both comparing aware-UTC instants (never naive):
- `expire_documents`: CNH/CRLV/MEI past their `expires_at` transition approved →
  expired (the courier must re-upload). Swept in a single indexed query
  (ix_courier_documents_expires_at — no N+1).
- `escalate_stale_reviews`: documents `pending` for ≥48h are escalated — audited
  (`kyc.escalated_48h`) so the area admin (and the platform admin) gain
  visibility (E5). The clock is injectable so tests use a fake `now`.

Logs start/finish/failure by doc_id WITHOUT PII.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.couriers.models import CourierDocument
from app.couriers.state_machine import assert_document_transition
from app.db.mixins import ensure_aware_utc

logger = structlog.get_logger("workers.document_expiry")

# Escalation threshold (E5): a document pending review for this long is escalated.
ESCALATION_AFTER = timedelta(hours=48)


async def expire_documents(session: AsyncSession, *, now: datetime | None = None) -> int:
    """Transition approved documents past expires_at → expired. Returns the count."""
    current = now or datetime.now(UTC)
    stmt = select(CourierDocument).where(
        CourierDocument.status == "approved",
        CourierDocument.expires_at.is_not(None),
    )
    expired = 0
    for doc in (await session.execute(stmt)).scalars().all():
        if doc.expires_at is None:
            continue
        if ensure_aware_utc(doc.expires_at) <= current:  # aware compare (TD-010)
            assert_document_transition(doc.status, "expired")
            doc.status = "expired"
            expired += 1
            logger.info("document_expired", document_id=doc.id)
            await write_audit(
                session,
                actor_id=None,
                action="kyc.document_expired",
                area_id=doc.area_id,
                after={"document_id": doc.id, "kind": doc.kind},
            )
    return expired


async def escalate_stale_reviews(session: AsyncSession, *, now: datetime | None = None) -> int:
    """Escalate documents pending review ≥48h (E5). Returns the count escalated."""
    current = now or datetime.now(UTC)
    cutoff = current - ESCALATION_AFTER
    stmt = select(CourierDocument).where(
        CourierDocument.status == "pending",
        CourierDocument.submitted_at.is_not(None),
    )
    escalated = 0
    for doc in (await session.execute(stmt)).scalars().all():
        if doc.submitted_at is None:
            continue
        if ensure_aware_utc(doc.submitted_at) <= cutoff:  # aware compare (TD-010)
            escalated += 1
            logger.warning("kyc_escalated_48h", document_id=doc.id)
            await write_audit(
                session,
                actor_id=None,
                action="kyc.escalated_48h",
                area_id=doc.area_id,
                after={"document_id": doc.id, "kind": doc.kind},
            )
    return escalated


async def expire_documents_task(ctx: dict[str, Any]) -> int:
    """arq entrypoint: sweep expired documents (session from worker ctx)."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        count = await expire_documents(session)
        await session.commit()
    return count


async def escalate_stale_reviews_task(ctx: dict[str, Any]) -> int:
    """arq entrypoint: escalate stale (≥48h) pending reviews."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        count = await escalate_stale_reviews(session)
        await session.commit()
    return count
