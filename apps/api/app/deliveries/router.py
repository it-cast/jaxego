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
from app.core.config import get_settings

router = APIRouter(prefix="/deliveries", tags=["deliveries"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _delivery_out(delivery, recipient, courier_name: str | None = None) -> DeliveryOut:
    """Serialize a delivery for the store; recipient phone is MASKED (TH-04)."""
    created = delivery.created_at.isoformat() if delivery.created_at else None
    scheduled = delivery.scheduled_at.isoformat() if delivery.scheduled_at else None
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
        price_cents=delivery.price_cents,
        fee_cents=delivery.fee_cents,
        has_image=delivery.image_key is not None,
        reference_number=delivery.reference_number,
        recipient_name=recipient.name if recipient else None,
        recipient_phone_masked=(mask_phone_display(recipient.phone_e164) if recipient else None),
        courier_id=delivery.courier_id,
        courier_name=courier_name,
        created_at=created,
        scheduled_at=scheduled,
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
    # Kick off the cascade only for immediate deliveries (Phase 8 — RN-009 / D-01).
    # Scheduled deliveries (AGENDADA) are released by the Inngest webhook.
    if result.state != "AGENDADA":
        from app.workers.dispatch import enqueue_dispatch

        await enqueue_dispatch(result.delivery_id)
    return result


@router.post("/scheduled/release", status_code=status.HTTP_200_OK)
async def inngest_release_scheduled(
    request: Request,
    session: SessionDep,
) -> dict:
    """Inngest webhook — transition AGENDADA → CRIADA and enqueue dispatch.

    Called by Inngest at the delivery's `scheduled_at` time. Protected by
    HMAC-SHA256 signature verification (x-inngest-signature header). Returns 200
    in all cases so Inngest does not retry on a stale/cancelled delivery.
    """
    import hashlib
    import hmac
    import json as json_lib
    import structlog

    wh_logger = structlog.get_logger("deliveries.inngest_webhook")

    # Signature verification — skip in dev when no signing key is configured.
    signing_key = get_settings().inngest_signing_key
    if signing_key:
        sig_header = request.headers.get("x-inngest-signature", "")
        body_bytes = await request.body()
        # Header format: "t=<ts>&s=<hmac_hex>"
        parts = dict(p.split("=", 1) for p in sig_header.split("&") if "=" in p)
        ts = parts.get("t", "")
        received_sig = parts.get("s", "")
        expected = hmac.new(
            signing_key.encode(),
            msg=f"{ts}{body_bytes.decode()}".encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(received_sig, expected):
            wh_logger.warning("inngest_webhook.invalid_signature")
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid Inngest signature.")
        payload = json_lib.loads(body_bytes)
    else:
        payload = await request.json()

    # Inngest wraps the event data in {"event": {"data": {...}}}
    event_data = payload.get("event", {}).get("data", payload.get("data", {}))
    delivery_id = event_data.get("delivery_id")
    if not isinstance(delivery_id, int):
        wh_logger.warning("inngest_webhook.missing_delivery_id", payload=payload)
        return {"ok": False, "reason": "missing delivery_id"}

    released = await service.release_scheduled_delivery(session, delivery_id=delivery_id)
    if released:
        from app.workers.dispatch import enqueue_dispatch
        await enqueue_dispatch(delivery_id)
        wh_logger.info("inngest_webhook.released", delivery_id=delivery_id)

    return {"ok": True, "released": released}


@router.get("/teams-online")
async def teams_with_online_couriers(
    scope: MerchantScopeDep,
    session: SessionDep,
    dropoff_neighborhood_id: int | None = None,
) -> list[dict]:
    """Teams with their online couriers for the delivery form sidebar."""
    from sqlalchemy import func as sa_func, select
    from datetime import UTC, timedelta, datetime
    from app.teams.models import Team
    from app.couriers.models import Courier, CourierCoverageArea
    from app.ratings.models import CourierRating
    from app.couriers.models import CourierPricingTable
    from app.couriers.coverage import is_eligible

    teams = list(
        (await session.execute(
            select(Team).where(Team.area_id == scope.area_id, Team.deleted_at.is_(None)).order_by(Team.id)
        )).scalars().all()
    )
    couriers = list(
        (await session.execute(
            select(Courier).where(
                Courier.area_id == scope.area_id,
                Courier.is_online.is_(True),
                Courier.status == "active",
                Courier.deleted_at.is_(None),
            )
        )).scalars().all()
    )

    if dropoff_neighborhood_id is not None and couriers:
        cov_rows = list(
            (await session.execute(
                select(CourierCoverageArea).where(
                    CourierCoverageArea.area_id == scope.area_id,
                    CourierCoverageArea.courier_id.in_([c.id for c in couriers]),
                )
            )).scalars().all()
        )
        cov_by: dict[int, list] = {}
        for row in cov_rows:
            cov_by.setdefault(row.courier_id, []).append(row)
        couriers = [
            c for c in couriers
            if is_eligible(cov_by.get(c.id, []), dropoff_neighborhood_id, dropoff_neighborhood_id)
        ]

    courier_ids = [c.id for c in couriers]

    ratings: dict[int, float] = {}
    if courier_ids:
        cutoff = datetime.now(UTC) - timedelta(days=90)
        rows = (await session.execute(
            select(
                CourierRating.courier_id,
                sa_func.avg(CourierRating.stars).label("avg"),
            ).where(
                CourierRating.courier_id.in_(courier_ids),
                CourierRating.created_at >= cutoff,
            ).group_by(CourierRating.courier_id)
        )).all()
        ratings = {int(r.courier_id): round(float(r.avg), 1) for r in rows}

    pricing: dict[int, int | None] = {}
    if courier_ids:
        price_rows = (await session.execute(
            select(CourierPricingTable).where(
                CourierPricingTable.courier_id.in_(courier_ids),
                CourierPricingTable.area_id == scope.area_id,
            )
        )).scalars().all()
        for pr in price_rows:
            if pr.courier_id not in pricing and pr.price is not None:
                pricing[pr.courier_id] = int(pr.price * 100)

    def courier_dict(c: Courier) -> dict:
        return {
            "id": c.id,
            "full_name": c.full_name,
            "avg_stars": ratings.get(c.id, 0.0),
            "price_cents": pricing.get(c.id),
        }

    result = []
    for team in teams:
        members = [c for c in couriers if c.team_id == team.id]
        result.append({
            "id": team.id,
            "name": team.name,
            "couriers": [courier_dict(c) for c in members],
        })

    return result


@router.get("/estimate")
async def estimate_delivery(
    dropoff_neighborhood_id: int,
    scope: MerchantScopeDep,
    session: SessionDep,
    team_id: int | None = None,
) -> dict:
    from app.deliveries.estimate import eligible_online_prices_cents, median_cents
    prices = await eligible_online_prices_cents(
        session,
        area_id=scope.area_id,
        pickup_nbhd_id=dropoff_neighborhood_id,
        dropoff_nbhd_id=dropoff_neighborhood_id,
        distance_m=None,
        team_id=team_id,
    )
    estimate = median_cents(prices)
    return {
        "price_cents": estimate,
        "courier_count": len(prices),
    }


@router.post("/{delivery_id}/image/presign")
async def presign_delivery_image(
    delivery_id: int,
    body: dict,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> dict:
    """Presign a PUT for the delivery product image."""
    import secrets
    from app.integrations.factory import get_storage_adapter

    delivery = await service.get_delivery(session, delivery_id=delivery_id, area_id=scope.area_id, merchant_id=scope.merchant_id)
    token = secrets.token_urlsafe(16)
    key = f"deliveries/{delivery.id}/{token}.webp"
    storage = get_storage_adapter()
    content_type = body.get("content_type", "image/jpeg")
    presign = await storage.presign_put(key, content_type=content_type, expires_in=300)
    delivery.image_key = key
    await session.commit()
    return {
        "presigned_url": presign.url,
        "method": presign.method,
        "headers": presign.headers,
        "key": key,
    }


@router.get("/{delivery_id}/image")
async def get_delivery_image(
    delivery_id: int,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> dict:
    """Presigned GET for the delivery product image."""
    from app.integrations.factory import get_storage_adapter

    delivery = await service.get_delivery(session, delivery_id=delivery_id, area_id=scope.area_id, merchant_id=scope.merchant_id)
    if not delivery.image_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sem imagem.")
    storage = get_storage_adapter()
    presign = await storage.presign_get(delivery.image_key, expires_in=180)
    return {"url": presign.url, "expires_in": 180}


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
            price_cents=d.price_cents,
            fee_cents=d.fee_cents,
            has_image=d.image_key is not None,
            reference_number=d.reference_number,
            recipient_name=r.name if r else None,
            recipient_phone_masked=mask_phone_display(r.phone_e164) if r else None,
            courier_id=d.courier_id,
            created_at=d.created_at.isoformat() if d.created_at else None,
            scheduled_at=d.scheduled_at.isoformat() if d.scheduled_at else None,
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
    courier_name: str | None = None
    if delivery.courier_id is not None:
        from app.couriers.models import Courier

        courier = await session.get(Courier, delivery.courier_id)
        if courier is not None:
            courier_name = courier.full_name
    return _delivery_out(delivery, recipient, courier_name=courier_name)


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
