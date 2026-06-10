"""Document expiry job (T-09 / TD-010) — aware-UTC, clock injected.

An approved document past its expires_at transitions to `expired` (the courier
must re-upload). A document not yet expired stays approved. The clock is injected
so the test is deterministic; comparisons never mix naive/aware (TD-010).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.couriers.models import CourierDocument
from app.workers.document_expiry import expire_documents

from tests.couriers.conftest import make_courier

NOW = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)


async def _approved_doc(session, courier, kind: str, expires_at):
    doc = CourierDocument(
        area_id=courier.area_id,
        courier_id=courier.id,
        kind=kind,
        status="approved",
        storage_key=f"couriers/{courier.id}/{kind}.webp",
        sha256="a" * 64,
        expires_at=expires_at,
    )
    session.add(doc)
    await session.flush()
    return doc


@pytest.mark.asyncio
async def test_expired_document_transitions(db_session, courier_seed) -> None:
    """An approved CNH past expires_at → expired."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc = await _approved_doc(db_session, courier, "cnh", NOW - timedelta(days=1))
    count = await expire_documents(db_session, now=NOW)
    assert count == 1
    await db_session.refresh(doc)
    assert doc.status == "expired"


@pytest.mark.asyncio
async def test_not_yet_expired_stays_approved(db_session, courier_seed) -> None:
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc = await _approved_doc(db_session, courier, "crlv", NOW + timedelta(days=30))
    count = await expire_documents(db_session, now=NOW)
    assert count == 0
    await db_session.refresh(doc)
    assert doc.status == "approved"


@pytest.mark.asyncio
async def test_document_without_expiry_ignored(db_session, courier_seed) -> None:
    """A selfie (no expires_at) is never swept by the expiry job."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc = await _approved_doc(db_session, courier, "selfie", None)
    count = await expire_documents(db_session, now=NOW)
    assert count == 0
    await db_session.refresh(doc)
    assert doc.status == "approved"


@pytest.mark.asyncio
async def test_naive_expiry_coerced_to_utc(db_session, courier_seed) -> None:
    """A naive expires_at read from the DB is coerced to UTC (TD-010 — no TypeError)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    # Naive datetime (as some drivers return) — must not crash the aware compare.
    naive_past = datetime(2026, 6, 9, 12, 0, 0)  # noqa: DTZ001 (intentional naive)
    doc = await _approved_doc(db_session, courier, "mei", naive_past)
    count = await expire_documents(db_session, now=NOW)
    assert count == 1
    await db_session.refresh(doc)
    assert doc.status == "expired"
