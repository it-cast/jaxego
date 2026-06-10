"""48h escalation job (T-09 / E5) — aware-UTC, clock injected.

A document `pending` review for ≥48h is escalated (audited `kyc.escalated_48h`),
giving the area admin and the platform admin visibility. A document pending for
<48h is not escalated. Comparisons are aware-UTC (TD-010); the clock is injected.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.audit.models import AuditLog
from app.couriers.models import CourierDocument
from app.workers.document_expiry import escalate_stale_reviews
from sqlalchemy import select

from tests.couriers.conftest import make_courier

NOW = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)


async def _pending_doc(session, courier, submitted_at):
    doc = CourierDocument(
        area_id=courier.area_id,
        courier_id=courier.id,
        kind="cnh",
        status="pending",
        storage_key=f"couriers/{courier.id}/cnh.webp",
        sha256="a" * 64,
        submitted_at=submitted_at,
    )
    session.add(doc)
    await session.flush()
    return doc


@pytest.mark.asyncio
async def test_stale_review_escalated(db_session, courier_seed) -> None:
    """A document pending ≥48h is escalated + audited (E5)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    await _pending_doc(db_session, courier, NOW - timedelta(hours=53))
    count = await escalate_stale_reviews(db_session, now=NOW)
    assert count == 1
    audits = (
        (await db_session.execute(select(AuditLog).where(AuditLog.action == "kyc.escalated_48h")))
        .scalars()
        .all()
    )
    assert len(audits) == 1


@pytest.mark.asyncio
async def test_fresh_review_not_escalated(db_session, courier_seed) -> None:
    """A document pending <48h is not escalated."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    await _pending_doc(db_session, courier, NOW - timedelta(hours=10))
    count = await escalate_stale_reviews(db_session, now=NOW)
    assert count == 0


@pytest.mark.asyncio
async def test_boundary_just_under_48h(db_session, courier_seed) -> None:
    """Just under 48h is NOT escalated (strict threshold)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    await _pending_doc(db_session, courier, NOW - timedelta(hours=47, minutes=59))
    count = await escalate_stale_reviews(db_session, now=NOW)
    assert count == 0
