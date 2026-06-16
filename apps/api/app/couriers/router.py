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
from app.core.logging import mask_email, mask_phone
from app.core.ratelimit import signup_rate_limit
from app.couriers import availability as availability_svc
from app.couriers import coverage as coverage_svc
from app.couriers import pricing as pricing_svc
from app.couriers import service
from app.couriers.models import Courier
from app.couriers.schemas import (
    AvailabilityBody,
    AvailabilityResponse,
    CourierAdminListItem,
    CourierAdminListOut,
    CourierDocumentItem,
    CourierProfileOut,
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
    mask_cpf_display,
)
from app.couriers.view import view_document_url
from app.db.session import get_session
from app.deliveries import service as delivery_service
from app.deliveries.schemas import (
    CourierDeliveryListItem,
    CourierDeliveryListOut,
    CourierDeliveryOut,
    mask_phone_display,
)
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
# Courier-facing delivery reads (F1.0 / MR-1). Self-only via _own_courier
# (IDOR → 404). PII reveal-by-state (RN-013): full dropoff + recipient only
# AFTER pickup (COLETADA+). `/active` is declared before `/{delivery_id}`.
# ---------------------------------------------------------------------------
_COURIER_DROPOFF_REVEALED = frozenset(
    {"COLETADA", "ENTREGUE", "RECUSADA_NO_DESTINO", "FINALIZADA"}
)


def _courier_delivery_out(delivery, recipient) -> CourierDeliveryOut:
    """Serialize a delivery for the assigned courier, hiding destination PII
    until pickup (RN-013). The recipient phone is masked even when revealed."""
    revealed = delivery.state in _COURIER_DROPOFF_REVEALED
    return CourierDeliveryOut(
        id=delivery.id,
        public_token=delivery.public_token,
        state=delivery.state,
        payment_method=delivery.payment_method,
        proof_method=delivery.proof_method,
        pickup_address=delivery.pickup_address,
        pickup_neighborhood=delivery.pickup_neighborhood,
        pickup_lat=delivery.pickup_lat,
        pickup_lng=delivery.pickup_lng,
        dropoff_neighborhood_id=delivery.dropoff_neighborhood_id,
        distance_m=delivery.distance_m,
        dropoff_address=delivery.dropoff_address if revealed else None,
        dropoff_number=delivery.dropoff_number if revealed else None,
        dropoff_complement=delivery.dropoff_complement if revealed else None,
        dropoff_lat=delivery.dropoff_lat if revealed else None,
        dropoff_lng=delivery.dropoff_lng if revealed else None,
        recipient_name=(recipient.name if recipient else None) if revealed else None,
        recipient_phone_masked=(
            mask_phone_display(recipient.phone_e164) if recipient else None
        )
        if revealed
        else None,
        estimate_min_cents=delivery.estimate_min_cents,
        estimate_max_cents=delivery.estimate_max_cents,
        fee_cents=delivery.fee_cents,
        reference_number=delivery.reference_number,
        items_description=delivery.items_description,
        items_quantity=delivery.items_quantity,
        created_at=delivery.created_at.isoformat() if delivery.created_at else None,
    )


@router.get("/{courier_id}/deliveries/active", response_model=CourierDeliveryOut | None)
async def get_active_delivery(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> CourierDeliveryOut | None:
    """The courier's current in-progress delivery (ACEITA/COLETADA), or null."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    result = await delivery_service.get_courier_active_delivery(session, courier_id=courier.id)
    if result is None:
        return None
    return _courier_delivery_out(*result)


@router.get("/{courier_id}/deliveries", response_model=CourierDeliveryListOut)
async def list_courier_deliveries(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> CourierDeliveryListOut:
    """The courier's delivery history, paginated (screen lista; no recipient PII)."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    page = await delivery_service.list_courier_deliveries(
        session, courier_id=courier.id, limit=min(limit, 100), offset=max(offset, 0)
    )
    items = [
        CourierDeliveryListItem(
            id=d.id,
            public_token=d.public_token,
            state=d.state,
            payment_method=d.payment_method,
            dropoff_neighborhood_id=d.dropoff_neighborhood_id,
            distance_m=d.distance_m,
            estimate_min_cents=d.estimate_min_cents,
            estimate_max_cents=d.estimate_max_cents,
            fee_cents=d.fee_cents,
            created_at=d.created_at.isoformat() if d.created_at else None,
        )
        for d, _ in page.items
    ]
    return CourierDeliveryListOut(
        items=items, total=page.total, limit=page.limit, offset=page.offset
    )


@router.get("/{courier_id}/deliveries/{delivery_id}", response_model=CourierDeliveryOut)
async def get_courier_delivery(
    courier_id: int,
    delivery_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> CourierDeliveryOut:
    """Read one delivery assigned to this courier (404 if not theirs — TH-03)."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    delivery, recipient = await delivery_service.get_courier_delivery(
        session, courier_id=courier.id, delivery_id=delivery_id
    )
    return _courier_delivery_out(delivery, recipient)


@router.get("/{courier_id}/profile", response_model=CourierProfileOut)
async def get_courier_profile(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> CourierProfileOut:
    """The courier's OWN profile (F1.6): identity + documents, PII masked. Self-only."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    docs = await service.list_courier_documents(session, courier_id=courier.id)
    return CourierProfileOut(
        id=courier.id,
        full_name=courier.full_name,
        cpf_masked=mask_cpf_display(courier.cpf),
        phone_masked=mask_phone(courier.phone_e164),
        email_masked=mask_email(courier.email),
        vehicle_type=courier.vehicle_type,
        vehicle_plate=courier.vehicle_plate,
        kyc_level=courier.kyc_level,
        status=courier.status,
        mei_pending=courier.mei_pending,
        documents=[CourierDocumentItem(kind=d.kind, status=d.status) for d in docs],
    )


# ---------------------------------------------------------------------------
# Admin of the area — review item-a-item (TH-09: area in the WHERE clause).
# ---------------------------------------------------------------------------
@admin_router.get("", response_model=CourierAdminListOut)
async def list_area_couriers(
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> CourierAdminListOut:
    """List couriers in the area (F2.0). `status=pending_kyc` powers the KYC queue;
    no filter lists everyone. Area in the WHERE clause (TH-09); platform admin
    (scope=None) sees all areas. CPF masked (TH-05)."""
    rows, total = await service.list_area_couriers(
        session,
        area_id=scope,
        status=status,
        limit=min(limit, 100),
        offset=max(offset, 0),
    )
    items = [
        CourierAdminListItem(
            id=c.id,
            full_name=c.full_name,
            cpf_masked=mask_cpf_display(c.cpf),
            status=c.status,
            kyc_level=c.kyc_level,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in rows
    ]
    return CourierAdminListOut(
        items=items, total=total, limit=min(limit, 100), offset=max(offset, 0)
    )


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
