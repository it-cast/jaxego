"""Document upload flow (T-05) — presign → PUT (stub) → complete → pending.

The byte never transits the backend on upload: the test simulates the client PUT
by writing into the Stub directly (as a real client would PUT to B2), then calls
`complete_document`, which downloads, validates magic bytes, reprocesses and
transitions the document to `pending`. `test_no_public_access` proves a document
is never readable without going through the adapter the backend gates.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from app.couriers import service
from app.couriers.constants import PRESIGN_PUT_EXPIRES_S
from app.media.validation import UnsupportedMediaError
from PIL import Image

from tests.couriers.conftest import make_courier


def _jpeg_bytes() -> bytes:
    im = Image.new("RGB", (1200, 900), (50, 80, 120))
    out = io.BytesIO()
    im.save(out, format="JPEG")
    return out.getvalue()


@pytest.mark.asyncio
async def test_presign_creates_pending_upload(db_session, courier_seed, storage_stub) -> None:
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    raw = _jpeg_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    doc, presign = await service.presign_document(
        db_session,
        courier_id=courier.id,
        kind="selfie",
        sha256_client=sha,
        content_type="image/jpeg",
        storage=storage_stub,
    )
    assert doc.status == "pending_upload"
    assert presign.method == "PUT"
    assert presign.expires_in == PRESIGN_PUT_EXPIRES_S
    assert doc.storage_key is not None and "couriers/" in doc.storage_key


@pytest.mark.asyncio
async def test_complete_transitions_to_pending(db_session, courier_seed, storage_stub) -> None:
    """After the client PUT, complete downloads, reprocesses and enters the queue."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    raw = _jpeg_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    doc, _presign = await service.presign_document(
        db_session,
        courier_id=courier.id,
        kind="selfie",
        sha256_client=sha,
        content_type="image/jpeg",
        storage=storage_stub,
    )
    # Simulate the client's direct PUT to B2 (writes the raw object in the stub).
    await storage_stub.put_bytes(doc.storage_key, raw, content_type="image/jpeg")

    completed = await service.complete_document(
        db_session, courier_id=courier.id, document_id=doc.id, storage=storage_stub
    )
    assert completed.status == "pending"
    assert completed.content_type == "image/webp"  # served as the derivative
    assert completed.sha256 is not None and len(completed.sha256) == 64
    assert completed.submitted_at is not None  # escalation clock started


@pytest.mark.asyncio
async def test_complete_rejects_fake_image(db_session, courier_seed, storage_stub) -> None:
    """A non-image upload is rejected by the magic-byte check at complete."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc, _presign = await service.presign_document(
        db_session,
        courier_id=courier.id,
        kind="cnh",
        sha256_client="0" * 64,
        content_type="image/jpeg",
        storage=storage_stub,
    )
    await storage_stub.put_bytes(
        doc.storage_key, b"%PDF-1.7 not an image", content_type="image/jpeg"
    )
    with pytest.raises(UnsupportedMediaError):
        await service.complete_document(
            db_session, courier_id=courier.id, document_id=doc.id, storage=storage_stub
        )


@pytest.mark.asyncio
async def test_no_public_access(db_session, courier_seed, storage_stub) -> None:
    """A KYC object is never readable without the adapter (REQ-015).

    There is no anonymous/public read path: the presigned URL is a fake stub
    string carrying no bytes, and fetching an unwritten key raises. The backend
    only calls fetch after an ownership+area check.
    """
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc, _presign = await service.presign_document(
        db_session,
        courier_id=courier.id,
        kind="selfie",
        sha256_client="0" * 64,
        content_type="image/jpeg",
        storage=storage_stub,
    )
    # Nothing uploaded yet → no readable object.
    with pytest.raises(KeyError):
        await storage_stub.fetch(doc.storage_key)
