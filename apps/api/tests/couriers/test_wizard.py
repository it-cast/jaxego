"""F-02 wizard resumption (E1) — server-side draft survives (T-05).

The courier row IS the persisted draft: a courier left in `pending_kyc` survives
across sessions, and documents already uploaded keep their state (the wizard shows
them as "enviado", never re-uploads). This is the server side of E1 (30-day
resumption); the date-based 30-day pruning is a Phase 14 retention job, but the
draft persistence is here.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from app.couriers import service
from app.couriers.schemas import CourierSignupBody
from PIL import Image

from tests.couriers.conftest import make_courier


def _body(area_id: int) -> CourierSignupBody:
    return CourierSignupBody.model_validate(
        {
            "area_id": area_id,
            "cpf": "39053344705",
            "full_name": "João Entregador",
            "phone_e164": "+5522999990000",
            "email": "joao@example.com",
            "password": "correct-horse-staple-10",
            "vehicle_type": "moto",
            "vehicle_plate": "ABC1D23",
            "consent": True,
        }
    )


def _jpeg() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (800, 600), (10, 20, 30)).save(out, format="JPEG")
    return out.getvalue()


@pytest.mark.asyncio
async def test_draft_survives_resumption(db_session, courier_seed) -> None:
    """A pending_kyc courier is a persisted draft retrievable later (E1)."""
    result = await service.signup(db_session, body=_body(courier_seed["area_a_id"]))
    await db_session.commit()

    # A later session retrieves the same draft (still pending_kyc).
    reloaded = await service.get_courier(db_session, result.courier_id)
    assert reloaded.status == "pending_kyc"
    assert reloaded.cpf == "39053344705"


@pytest.mark.asyncio
async def test_uploaded_document_survives_resumption(
    db_session, courier_seed, storage_stub
) -> None:
    """A document already in `pending` keeps its state across resumption (E1)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    raw = _jpeg()
    sha = hashlib.sha256(raw).hexdigest()
    doc, _p = await service.presign_document(
        db_session,
        courier_id=courier.id,
        kind="selfie",
        sha256_client=sha,
        content_type="image/jpeg",
        storage=storage_stub,
    )
    await storage_stub.put_bytes(doc.storage_key, raw, content_type="image/jpeg")
    await service.complete_document(
        db_session, courier_id=courier.id, document_id=doc.id, storage=storage_stub
    )
    await db_session.commit()

    # Re-fetch: the document is still pending (no re-upload needed).
    again = await service.get_document_for_scope(
        db_session, document_id=doc.id, courier_id=courier.id, area_id=None
    )
    assert again.status == "pending"
    assert again.sha256 is not None
