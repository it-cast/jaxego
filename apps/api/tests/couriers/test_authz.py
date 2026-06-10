"""IDOR / cross-area authorization on courier documents (T-05 / TH-03).

`get_document_for_scope` puts the area in the WHERE clause: a document in area A
is invisible to an admin scoped to area B — the result is a 404 (DocumentNotFound),
never a 403, so existence is not leaked. The platform-admin scope (area_id=None)
sees across areas (audited by the caller).
"""

from __future__ import annotations

import pytest
from app.couriers import service

from tests.couriers.conftest import make_courier


async def _courier_with_doc(session, *, area_id: int, user_id: int):
    courier = await make_courier(session, area_id=area_id, user_id=user_id)
    from app.couriers.models import CourierDocument

    doc = CourierDocument(
        area_id=area_id,
        courier_id=courier.id,
        kind="selfie",
        status="pending",
        storage_key=f"couriers/{courier.id}/x.webp",
    )
    session.add(doc)
    await session.flush()
    return courier, doc


@pytest.mark.asyncio
async def test_cross_area_document_is_404(db_session, courier_seed) -> None:
    """An admin scoped to area B cannot read a document in area A → 404."""
    courier, doc = await _courier_with_doc(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    with pytest.raises(service.DocumentNotFoundError):
        await service.get_document_for_scope(
            db_session,
            document_id=doc.id,
            courier_id=courier.id,
            area_id=courier_seed["area_b_id"],  # wrong area scope
        )


@pytest.mark.asyncio
async def test_in_area_document_resolves(db_session, courier_seed) -> None:
    """The owning area's admin resolves the document normally."""
    courier, doc = await _courier_with_doc(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    found = await service.get_document_for_scope(
        db_session,
        document_id=doc.id,
        courier_id=courier.id,
        area_id=courier_seed["area_a_id"],
    )
    assert found.id == doc.id


@pytest.mark.asyncio
async def test_platform_scope_sees_cross_area(db_session, courier_seed) -> None:
    """The platform-admin scope (None) resolves cross-area (audited by caller)."""
    courier, doc = await _courier_with_doc(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    found = await service.get_document_for_scope(
        db_session, document_id=doc.id, courier_id=courier.id, area_id=None
    )
    assert found.id == doc.id


@pytest.mark.asyncio
async def test_wrong_courier_id_is_404(db_session, courier_seed) -> None:
    """A document id paired with the wrong courier id → 404 (ownership in WHERE)."""
    courier, doc = await _courier_with_doc(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    with pytest.raises(service.DocumentNotFoundError):
        await service.get_document_for_scope(
            db_session,
            document_id=doc.id,
            courier_id=courier.id + 999,
            area_id=courier_seed["area_a_id"],
        )
