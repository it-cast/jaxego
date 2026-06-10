"""Document reprocess job (T-05) — runs the validate/reprocess pipeline async.

In production the `complete` request enqueues this job so the CPU work (download
+ Pillow) happens OUTSIDE the HTTP request. The job downloads the raw object,
validates magic bytes, reprocesses to WebP (strip EXIF), confirms the SHA-256 and
rewrites the derivative, then transitions the document to `pending`. Logs
start/finish/failure by doc_id WITHOUT PII (no content, no key in logs).
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers import documents as docs_mod
from app.couriers.models import CourierDocument
from app.integrations.factory import get_storage_adapter

logger = structlog.get_logger("workers.document_reprocess")


async def reprocess_document(session: AsyncSession, *, document_id: int) -> bool:
    """Reprocess one document; True on success. Pure logic (testable, no arq ctx)."""
    doc = await session.get(CourierDocument, document_id)
    if doc is None or doc.status != "pending_upload":
        return False
    logger.info("reprocess_start", document_id=document_id)
    try:
        await docs_mod.complete_upload(session, doc=doc, storage=get_storage_adapter())
    except Exception:  # noqa: BLE001 — failure is logged without PII; caller retries
        logger.warning("reprocess_failed", document_id=document_id)
        return False
    logger.info("reprocess_done", document_id=document_id, status=doc.status)
    return True


async def reprocess_document_task(ctx: dict[str, Any], document_id: int) -> bool:
    """arq entrypoint: reprocess one document (session from the worker ctx)."""
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        ok = await reprocess_document(session, document_id=document_id)
        await session.commit()
    return ok
