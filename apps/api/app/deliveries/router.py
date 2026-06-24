"""/v1/deliveries — store creates, lists and cancels deliveries (F-03).

Every route resolves the store via `merchant_scope` (A01 / TH-03): the
(area_id, merchant_id) pair is pushed into the service WHERE clause, so a delivery
from another store/area returns 404 (no existence leak). Create is rate-limited
per store (TH-07) and idempotent via an optional `Idempotency-Key` header. The
request body carries recipient PII and is NEVER logged (TH-04). `commit()` happens
in the router (the phase pattern).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import RateLimitedError
from app.db.session import get_session
from app.deliveries import service
from app.deliveries.dependencies import MerchantScopeDep
from app.deliveries.schemas import (
    CancelDeliveryBody,
    CreateDeliveryBody,
    CreateDeliveryResponse,
    DeliveryListItem,
    DeliveryListOut,
    DeliveryOut,
    mask_phone_display,
)
from app.deliveries.service import delivery_create_limiter

router = APIRouter(prefix="/deliveries", tags=["deliveries"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _delivery_out(delivery, recipient) -> DeliveryOut:
    """Serialize a delivery for the store; recipient phone is MASKED (TH-04)."""
    created = delivery.created_at.isoformat() if delivery.created_at else None
    return DeliveryOut(
        id=delivery.id,
        public_token=delivery.public_token,
        state=delivery.state,
        payment_method=delivery.payment_method,
        proof_method=delivery.proof_method,
        dropoff_address=delivery.dropoff_address,
        dropoff_number=delivery.dropoff_number,
        dropoff_complement=delivery.dropoff_complement,
        dropoff_neighborhood_id=delivery.dropoff_neighborhood_id,
        distance_m=delivery.distance_m,
        dropoff_lat=delivery.dropoff_lat,
        dropoff_lng=delivery.dropoff_lng,
        weight_g=delivery.weight_g,
        length_cm=delivery.length_cm,
        width_cm=delivery.width_cm,
        height_cm=delivery.height_cm,
        estimate_min_cents=delivery.estimate_min_cents,
        estimate_max_cents=delivery.estimate_max_cents,
        fee_cents=delivery.fee_cents,
        reference_number=delivery.reference_number,
        recipient_name=recipient.name if recipient else None,
        recipient_phone_masked=(mask_phone_display(recipient.phone_e164) if recipient else None),
        courier_id=delivery.courier_id,
        created_at=created,
    )


@router.post("", response_model=CreateDeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    body: CreateDeliveryBody,
    request: Request,
    scope: MerchantScopeDep,
    session: SessionDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CreateDeliveryResponse:
    """Create a delivery (F-03). `direct` is free; card/pix charges a split first (E3)."""
    delivery_create_limiter.check(f"merchant:{scope.merchant_id}")
    # Phase 10: wire the PaymentService for card/pix (circuit breaker: a gateway outage
    # surfaces as a handled error on card/pix and NEVER blocks `direct`).
    payment_service = None
    if body.payment_method.value != "direct":
        from app.payments.factory import get_payment_adapter
        from app.payments.service import PaymentService

        payment_service = PaymentService(session, payment=get_payment_adapter())
    result = await service.create_delivery(
        session,
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        actor_user_id=scope.user_id,
        body=body,
        ip=_client_ip(request),
        payment_service=payment_service,
        card_blob=body.card_blob,
        customer_document=body.payer_document,
        customer_email=str(body.payer_email) if body.payer_email else None,
    )
    await session.commit()
    # Kick off the cascade (Phase 8) — enqueued, never inline (RN-009 / D-01).
    from app.workers.dispatch import enqueue_dispatch

    await enqueue_dispatch(result.delivery_id)
    return result


@router.get("/estimate")
async def estimate_delivery(
    dropoff_neighborhood_id: int,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> dict:
    from app.deliveries.estimate import eligible_online_prices_cents, median_cents
    prices = await eligible_online_prices_cents(
        session,
        area_id=scope.area_id,
        pickup_nbhd_id=dropoff_neighborhood_id,
        dropoff_nbhd_id=dropoff_neighborhood_id,
        distance_m=None,
    )
    estimate = median_cents(prices)
    return {
        "estimate_min_cents": estimate,
        "estimate_max_cents": estimate,
        "courier_count": len(prices),
    }


@router.get("", response_model=DeliveryListOut)
async def list_deliveries(
    scope: MerchantScopeDep,
    session: SessionDep,
    state: str | None = None,
    payment_method: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> DeliveryListOut:
    """List the store's deliveries, paginated (screen 14). No N+1; phone masked."""
    page = await service.list_deliveries(
        session,
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        state=state,
        payment_method=payment_method,
        limit=min(limit, 100),
        offset=max(offset, 0),
    )
    items = [
        DeliveryListItem(
            id=d.id,
            public_token=d.public_token,
            state=d.state,
            payment_method=d.payment_method,
            dropoff_neighborhood_id=d.dropoff_neighborhood_id,
            estimate_min_cents=d.estimate_min_cents,
            estimate_max_cents=d.estimate_max_cents,
            fee_cents=d.fee_cents,
            reference_number=d.reference_number,
            recipient_name=r.name if r else None,
            recipient_phone_masked=mask_phone_display(r.phone_e164) if r else None,
            courier_id=d.courier_id,
            created_at=d.created_at.isoformat() if d.created_at else None,
        )
        for d, r in page.items
    ]
    return DeliveryListOut(items=items, total=page.total, limit=page.limit, offset=page.offset)


@router.get("/{delivery_id}", response_model=DeliveryOut)
async def get_delivery(
    delivery_id: int,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> DeliveryOut:
    """Read one of the store's deliveries (404 if not owned — TH-03)."""
    delivery = await service.get_delivery(
        session,
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        delivery_id=delivery_id,
    )
    recipient = None
    if delivery.recipient_id is not None:
        from app.deliveries.models import Recipient

        recipient = await session.get(Recipient, delivery.recipient_id)
    return _delivery_out(delivery, recipient)


@router.post("/{delivery_id}/cancel", response_model=DeliveryOut)
async def cancel_delivery(
    delivery_id: int,
    body: CancelDeliveryBody,
    request: Request,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> DeliveryOut:
    """Cancel a delivery before acceptance (CRIADA → CANCELADA, zero cost RN-004)."""
    delivery = await service.cancel_delivery(
        session,
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        actor_user_id=scope.user_id,
        delivery_id=delivery_id,
        reason=body.reason,
        ip=_client_ip(request),
    )
    await session.commit()
    # E4 (D-07): cancel any pending offer/cascade — zero cost, RN-004. Best-effort.
    from app.core.redis import get_redis_client
    from app.dispatch import service as dispatch_service

    await dispatch_service.cancel_pending_offers(get_redis_client(), delivery_id=delivery_id)
    recipient = None
    if delivery.recipient_id is not None:
        from app.deliveries.models import Recipient

        recipient = await session.get(Recipient, delivery.recipient_id)
    return _delivery_out(delivery, recipient)


__all__ = ["router", "RateLimitedError"]
