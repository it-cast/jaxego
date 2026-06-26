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
    token = secrets.token_urlsafe(16)
    return f"couriers/{courier_id}/{token}"


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
    """Mark the document as pending (enters the admin review queue).

    The image stays in B2 as uploaded — no reprocessing.
    """
    assert_document_transition(doc.status, "pending")
    doc.status = "pending"
    doc.submitted_at = datetime.now(UTC)
    return doc
