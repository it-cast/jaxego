"""Admin document viewer — short-lived presigned GET, audited (T-06 / TH-01).

The admin of the area gets a ≤180s presigned GET for the document derivative.
Ownership+area are in the WHERE clause (TH-03) — a document outside the admin's
scope is a 404, never a 403 (no existence leak). The ACCESS is audited
(`kyc.document_viewed`) WITHOUT the content (only doc_id + actor — A09/LGPD).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.couriers import service
from app.couriers.constants import PRESIGN_GET_EXPIRES_S
from app.integrations.base import StoragePort


class DocumentNotReadyError(service.AppError):
    """The document has no stored object yet (still pending_upload)."""

    status_code = 422
    code = "document_not_ready"

    def __init__(self) -> None:
        super().__init__("Documento ainda não foi enviado.")


async def view_document_url(
    session: AsyncSession,
    *,
    courier_id: int,
    document_id: int,
    area_id: int | None,
    actor_id: int,
    storage: StoragePort,
) -> tuple[str, int]:
    """Return (presigned_get_url, expires_in) for the admin viewer, audited."""
    doc = await service.get_document_for_scope(
        session, document_id=document_id, courier_id=courier_id, area_id=area_id
    )
    if doc.storage_key is None:
        raise DocumentNotReadyError()

    pres = await storage.presign_get(doc.storage_key, expires_in=PRESIGN_GET_EXPIRES_S)
    await write_audit(
        session,
        actor_id=actor_id,
        action="kyc.document_viewed",  # PII access — logged WITHOUT content (A09)
        area_id=doc.area_id,
        after={"document_id": doc.id},
        cross_area_bypass=area_id is None,
    )
    return pres.url, pres.expires_in
