"""Document presign + post-upload reprocess orchestration (T-05).

Three moments (RESEARCH Architecture):
1. `issue_presign` — create the courier_document row (pending_upload), generate a
   server-side key (ULID-based, NO CPF — TH-11), and return a presigned PUT
   (≤300s). The byte never transits the backend.
2. `complete_upload` — after the client reports the PUT done, download the raw
   object (SSRF-guarded inside the adapter), validate magic bytes, reprocess with
   Pillow (resize/WebP/strip EXIF), confirm the derivative SHA-256, write the
   derivative back, and transition pending_upload → pending.

The reprocess is CPU work; in production it runs in the arq worker
(`workers/document_reprocess.py`). The pure orchestration lives here so it is unit-
testable against the Stub.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.constants import PRESIGN_PUT_EXPIRES_S
from app.couriers.models import Courier, CourierDocument
from app.couriers.state_machine import assert_document_transition
from app.integrations.base import PresignResult, StoragePort
from app.media.reprocess import reprocess_to_webp


def _new_key(courier_id: int) -> str:
    """A non-sequential object key under the courier's prefix (TH-11).

    No CPF, no user input — `couriers/{courier_id}/{random}.webp`. The random
    token is URL-safe and unguessable; the derivative is always WebP.
    """
    token = secrets.token_urlsafe(16)
    return f"couriers/{courier_id}/{token}.webp"


async def issue_presign(
    session: AsyncSession,
    *,
    courier: Courier,
    kind: str,
    sha256_client: str,
    content_type: str,
    storage: StoragePort,
) -> tuple[CourierDocument, PresignResult]:
    """Create a pending_upload document + a presigned PUT (≤300s).

    The presign content-type is the RAW upload's (what the client will PUT); the
    stored derivative is always image/webp after reprocess.
    """
    key = _new_key(courier.id)
    doc = CourierDocument(
        area_id=courier.area_id,
        courier_id=courier.id,
        kind=kind,
        status="pending_upload",
        storage_key=key,
        sha256_client=sha256_client,
    )
    session.add(doc)
    await session.flush()

    presign = await storage.presign_put(
        key, content_type=content_type, expires_in=PRESIGN_PUT_EXPIRES_S
    )
    return doc, presign


async def complete_upload(
    session: AsyncSession,
    *,
    doc: CourierDocument,
    storage: StoragePort,
) -> CourierDocument:
    """Download → validate → reprocess → rewrite derivative → pending.

    Raises UnsupportedMediaError (422) if the uploaded bytes fail the magic-byte
    check. On success the document carries the derivative's SHA-256 (TH-07) and
    transitions to `pending` (enters the admin review queue).
    """
    assert doc.storage_key is not None
    raw = await storage.fetch(doc.storage_key)
    # Validate magic bytes + reprocess (resize/WebP/strip EXIF) + hash derivative.
    derived, sha = reprocess_to_webp(raw)
    # Overwrite the object with the clean derivative (never serve the raw byte).
    await storage.put_bytes(doc.storage_key, derived, content_type="image/webp")

    assert_document_transition(doc.status, "pending")
    doc.status = "pending"
    doc.content_type = "image/webp"
    doc.sha256 = sha
    # Escalation 48h clock (E5) starts when the item enters the review queue.
    doc.submitted_at = datetime.now(UTC)  # aware UTC (TD-010)
    return doc
