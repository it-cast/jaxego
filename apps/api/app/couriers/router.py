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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.auth.models import User
from app.core.exceptions import NotFoundError
from app.core.ratelimit import signup_rate_limit
from app.couriers import availability as availability_svc
from app.couriers import coverage as coverage_svc
from app.couriers import pricing as pricing_svc
from app.couriers import service
from app.couriers.models import Courier
from app.couriers.schemas import (
    AvailabilityBody,
    AvailabilityResponse,
    CourierSignupBody,
    CourierSignupResponse,
    CoverageBody,
    CoverageRowRead,
    DocumentPresignBody,
    DocumentPresignResponse,
    DocumentReadResponse,
    DocumentReviewBody,
    DocumentReviewResponse,
    MeiBody,
    MeiResponse,
    PricingBody,
    PricingRowRead,
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
# Phase 6 — the courier manages their OWN coverage / pricing / availability.
# Self-only: the courier id in the path must belong to the authenticated user AND
# (for non-platform users) be inside the token's area scope. Any mismatch → 404
# (no existence leak — TH-03/item 2 of the Security Notes).
# ---------------------------------------------------------------------------
async def _own_courier(
    session: AsyncSession, *, courier_id: int, user: User, scope: int | None
) -> Courier:
    stmt = select(Courier).where(Courier.id == courier_id, Courier.user_id == user.id)
    if scope is not None:
        stmt = stmt.where(Courier.area_id == scope)
    courier = (await session.execute(stmt)).scalar_one_or_none()
    if courier is None or courier.deleted_at is not None:
        raise NotFoundError("Entregador não encontrado.")
    return courier


@router.put("/{courier_id}/coverage", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def set_coverage(
    courier_id: int,
    body: CoverageBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> None:
    """The courier sets the neighborhoods they serve / refuse (RN-003, self-only)."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    await coverage_svc.set_coverage(
        session,
        area_id=courier.area_id,
        courier_id=courier.id,
        includes=body.includes,
        excludes=body.excludes,
    )
    await session.commit()


@router.get("/{courier_id}/coverage", response_model=list[CoverageRowRead])
async def get_coverage(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[CoverageRowRead]:
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    rows = await coverage_svc.list_coverage(session, area_id=courier.area_id, courier_id=courier.id)
    return [CoverageRowRead.model_validate(r) for r in rows]


@router.put("/{courier_id}/pricing", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def set_pricing(
    courier_id: int,
    body: PricingBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> None:
    """The courier sets the freight table; below the floor → 422 (RN-015, self-only)."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    await pricing_svc.set_pricing(
        session,
        area_id=courier.area_id,
        courier_id=courier.id,
        mode=body.mode,
        rows=body.rows,
    )
    await session.commit()


@router.get("/{courier_id}/pricing", response_model=list[PricingRowRead])
async def get_pricing(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[PricingRowRead]:
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    rows = await pricing_svc.list_pricing(session, area_id=courier.area_id, courier_id=courier.id)
    return [PricingRowRead.model_validate(r) for r in rows]


@router.patch("/{courier_id}/availability", response_model=AvailabilityResponse)
async def set_availability(
    courier_id: int,
    body: AvailabilityBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> AvailabilityResponse:
    """Toggle online/offline; only an `active` courier may go online (REQ-018)."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    updated = await availability_svc.set_availability(
        session, area_id=courier.area_id, courier_id=courier.id, online=body.online
    )
    await session.commit()
    # busy is DERIVED; the real active-delivery count arrives in Phase 7/8 (0 here).
    busy = availability_svc.compute_busy(active_deliveries=0, max_concurrent=updated.max_concurrent)
    return AvailabilityResponse(is_online=updated.is_online, busy=busy)


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
