"""KYC item-a-item review (T-06 / D-04 / E4).

Each document is approved/rejected INDEPENDENTLY: rejecting the CNH never
invalidates an already-approved selfie. A reject without a reason is blocked. A
courier becomes `active` only when EVERY required document for its level is
approved (RN-002). MEI is not a blocking item.
"""

from __future__ import annotations

import pytest
from app.couriers import service
from app.couriers.models import CourierDocument

from tests.couriers.conftest import make_courier


async def _pending_doc(session, courier, kind: str) -> CourierDocument:
    doc = CourierDocument(
        area_id=courier.area_id,
        courier_id=courier.id,
        kind=kind,
        status="pending",
        storage_key=f"couriers/{courier.id}/{kind}.webp",
        sha256="a" * 64,
    )
    session.add(doc)
    await session.flush()
    return doc


@pytest.mark.asyncio
async def test_reject_requires_reason(db_session, courier_seed) -> None:
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc = await _pending_doc(db_session, courier, "cnh")
    with pytest.raises(service.RejectReasonRequiredError):
        await service.review_document(
            db_session,
            courier_id=courier.id,
            document_id=doc.id,
            area_id=courier.area_id,
            actor_id=courier_seed["user_id"],
            action="reject",
            reason=None,
        )


@pytest.mark.asyncio
async def test_reject_cnh_keeps_selfie_approved(db_session, courier_seed) -> None:
    """E4 — rejecting the CNH does NOT invalidate the already-approved selfie."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    selfie = await _pending_doc(db_session, courier, "selfie")
    cnh = await _pending_doc(db_session, courier, "cnh")

    # Approve the selfie first.
    await service.review_document(
        db_session,
        courier_id=courier.id,
        document_id=selfie.id,
        area_id=courier.area_id,
        actor_id=courier_seed["user_id"],
        action="approve",
    )
    # Now reject the CNH.
    await service.review_document(
        db_session,
        courier_id=courier.id,
        document_id=cnh.id,
        area_id=courier.area_id,
        actor_id=courier_seed["user_id"],
        action="reject",
        reason="sem_ear",
        detail="CNH sem observação EAR.",
    )
    await db_session.refresh(selfie)
    await db_session.refresh(cnh)
    assert selfie.status == "approved"  # untouched
    assert cnh.status == "rejected"
    assert cnh.reject_reason == "sem_ear"


@pytest.mark.asyncio
async def test_rejected_item_can_reupload(db_session, courier_seed) -> None:
    """E4 — a rejected item returns to pending_upload (re-upload just that item)."""
    from app.couriers.state_machine import assert_document_transition

    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    cnh = await _pending_doc(db_session, courier, "cnh")
    await service.review_document(
        db_session,
        courier_id=courier.id,
        document_id=cnh.id,
        area_id=courier.area_id,
        actor_id=courier_seed["user_id"],
        action="reject",
        reason="ilegivel",
    )
    await db_session.refresh(cnh)
    # The rejected item may transition back to pending_upload (no exception).
    assert_document_transition(cnh.status, "pending_upload")


@pytest.mark.asyncio
async def test_all_required_approved_activates_courier(db_session, courier_seed) -> None:
    """RN-002 — courier activates when every required doc for the level is approved.

    area_a requires `completa` → selfie + cnh + crlv. Approving all three flips
    the courier to active.
    """
    courier = await make_courier(
        db_session,
        area_id=courier_seed["area_a_id"],
        user_id=courier_seed["user_id"],
        kyc_level="completa",
    )
    docs = {k: await _pending_doc(db_session, courier, k) for k in ("selfie", "cnh", "crlv")}

    last_status = "pending_kyc"
    for _kind, doc in docs.items():
        _doc, last_status = await service.review_document(
            db_session,
            courier_id=courier.id,
            document_id=doc.id,
            area_id=courier.area_id,
            actor_id=courier_seed["user_id"],
            action="approve",
        )
    assert last_status == "active"
    await db_session.refresh(courier)
    assert courier.status == "active"


@pytest.mark.asyncio
async def test_partial_approval_does_not_activate(db_session, courier_seed) -> None:
    """A courier stays pending_kyc until ALL required documents are approved."""
    courier = await make_courier(
        db_session,
        area_id=courier_seed["area_a_id"],
        user_id=courier_seed["user_id"],
        kyc_level="completa",
    )
    selfie = await _pending_doc(db_session, courier, "selfie")
    _doc, status = await service.review_document(
        db_session,
        courier_id=courier.id,
        document_id=selfie.id,
        area_id=courier.area_id,
        actor_id=courier_seed["user_id"],
        action="approve",
    )
    assert status == "pending_kyc"  # cnh + crlv still missing


@pytest.mark.asyncio
async def test_simples_level_activates_on_selfie(db_session, courier_seed) -> None:
    """A simples-level courier activates once the selfie is approved (RN-002)."""
    courier = await make_courier(
        db_session,
        area_id=courier_seed["area_b_id"],
        user_id=courier_seed["user_id"],
        kyc_level="simples",
    )
    selfie = await _pending_doc(db_session, courier, "selfie")
    _doc, status = await service.review_document(
        db_session,
        courier_id=courier.id,
        document_id=selfie.id,
        area_id=courier.area_id,
        actor_id=courier_seed["user_id"],
        action="approve",
    )
    assert status == "active"
