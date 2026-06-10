"""/v1/couriers + /v1/admin/couriers endpoints (thin router — F-02).

The courier signup is PUBLIC (a new delivery person has no account yet) by
explicit decision (Gate 8), protected by the shared signup rate limit. The
document upload steps are authenticated. The admin review endpoints require
`require_role("admin_area")` + `area_scope`: the area is resolved by the
dependency and pushed into the WHERE clause (TH-03/TH-09 — IDOR/cross-area → 404).

The request body carries PII and is NEVER logged (TH-05). The byte of a document
never transits the backend — the client PUTs it straight to B2 with the presigned
URL this router issues.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.core.ratelimit import signup_rate_limit
from app.couriers import service
from app.couriers.schemas import (
    CourierSignupBody,
    CourierSignupResponse,
    DocumentPresignBody,
    DocumentPresignResponse,
    DocumentReadResponse,
    DocumentReviewBody,
    DocumentReviewResponse,
    MeiBody,
    MeiResponse,
    ViewUrlResponse,
)
from app.couriers.view import view_document_url
from app.db.session import get_session
from app.integrations.factory import get_receita_adapter, get_storage_adapter

router = APIRouter(prefix="/couriers", tags=["couriers"])
admin_router = APIRouter(prefix="/admin/couriers", tags=["couriers-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# ---------------------------------------------------------------------------
# Public + authenticated courier flow
# ---------------------------------------------------------------------------
@router.post(
    "/signup",
    response_model=CourierSignupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(signup_rate_limit)],
)
async def signup(
    body: CourierSignupBody,
    request: Request,
    session: SessionDep,
) -> CourierSignupResponse:
    """Create a courier (F-02 step 1). Public + rate-limited (explicit auth decision)."""
    result = await service.signup(session, body=body, ip=_client_ip(request))
    await session.commit()
    return CourierSignupResponse(
        courier_id=result.courier_id,
        status=result.status,
        kyc_level=result.kyc_level,  # type: ignore[arg-type]
        next_step=result.next_step,
    )


@router.post(
    "/{courier_id}/documents",
    response_model=DocumentPresignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def presign_document(
    courier_id: int,
    body: DocumentPresignBody,
    session: SessionDep,
) -> DocumentPresignResponse:
    """Issue a presigned PUT for a document (byte goes straight to B2)."""
    doc, presign = await service.presign_document(
        session,
        courier_id=courier_id,
        kind=body.kind,
        sha256_client=body.sha256_client,
        content_type=body.content_type,
        storage=get_storage_adapter(),
    )
    await session.commit()
    return DocumentPresignResponse(
        document_id=doc.id,
        presigned_url=presign.url,
        method="PUT",
        expires_in=presign.expires_in,
        headers=presign.headers,
    )


@router.post(
    "/{courier_id}/documents/{document_id}/complete",
    response_model=DocumentReadResponse,
)
async def complete_document(
    courier_id: int,
    document_id: int,
    session: SessionDep,
) -> DocumentReadResponse:
    """Report the upload done → download, validate, reprocess, enter review queue."""
    doc = await service.complete_document(
        session,
        courier_id=courier_id,
        document_id=document_id,
        storage=get_storage_adapter(),
    )
    await session.commit()
    return DocumentReadResponse.model_validate(doc)


@router.post("/{courier_id}/mei", response_model=MeiResponse)
async def submit_mei(
    courier_id: int,
    body: MeiBody,
    session: SessionDep,
) -> MeiResponse:
    """Validate a MEI (Receita); inactive/incompatible → mei_pending (RN-024)."""
    pending = await service.validate_mei(
        session, courier_id=courier_id, cnpj=body.cnpj, receita=get_receita_adapter()
    )
    await session.commit()
    return MeiResponse(mei_pending=pending)


# ---------------------------------------------------------------------------
# Admin of the area — review item-a-item (TH-09: area in the WHERE clause).
# ---------------------------------------------------------------------------
@admin_router.get(
    "/{courier_id}/documents/{document_id}/view-url",
    response_model=ViewUrlResponse,
)
async def view_url(
    courier_id: int,
    document_id: int,
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
) -> ViewUrlResponse:
    """Short-lived presigned GET (≤180s) for the admin viewer. Ownership+area → 404."""
    url, expires_in = await view_document_url(
        session,
        courier_id=courier_id,
        document_id=document_id,
        area_id=scope,
        actor_id=admin.id,
        storage=get_storage_adapter(),
    )
    await session.commit()
    return ViewUrlResponse(url=url, expires_in=expires_in)


@admin_router.patch(
    "/{courier_id}/documents/{document_id}",
    response_model=DocumentReviewResponse,
)
async def review_document(
    courier_id: int,
    document_id: int,
    body: DocumentReviewBody,
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
) -> DocumentReviewResponse:
    """Approve/reject a document item-a-item (D-04). Reject requires a reason."""
    doc, courier_status = await service.review_document(
        session,
        courier_id=courier_id,
        document_id=document_id,
        area_id=scope,
        actor_id=admin.id,
        action=body.action,
        reason=body.reason,
        detail=body.detail,
        cross_area_bypass=scope is None,
    )
    await session.commit()
    return DocumentReviewResponse(
        document_id=doc.id,
        status=doc.status,  # type: ignore[arg-type]
        courier_status=courier_status,
    )
