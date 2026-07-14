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


def _delivery_out(
    delivery,
    recipient,
    courier_name: str | None = None,
    neighborhood_name: str | None = None,
    team_names: list[str] | None = None,
    courier_phone: str | None = None,
    courier_vehicle_type: str | None = None,
    courier_vehicle_plate: str | None = None,
    courier_rating: float | None = None,
    courier_rating_count: int = 0,
    courier_total_deliveries: int = 0,
    courier_since: str | None = None,
) -> DeliveryOut:
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
        dropoff_reference=delivery.dropoff_reference,
        dropoff_neighborhood_id=delivery.dropoff_neighborhood_id,
        dropoff_neighborhood_name=neighborhood_name,
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
        recipient_phone=(recipient.phone_e164 if recipient else None),
        courier_id=delivery.courier_id,
        courier_name=courier_name,
        courier_phone=courier_phone,
        courier_vehicle_type=courier_vehicle_type,
        courier_vehicle_plate=courier_vehicle_plate,
        courier_rating=courier_rating,
        courier_rating_count=courier_rating_count,
        courier_total_deliveries=courier_total_deliveries,
        courier_since=courier_since,
        items_description=delivery.items_description,
        items_quantity=delivery.items_quantity,
        notes=delivery.notes,
        pickup_address=delivery.pickup_address,
        pickup_neighborhood=delivery.pickup_neighborhood,
        team_names=team_names or [],
        created_at=created,
        scheduled_at=scheduled,
        pix_qr_code=delivery.pix_qr_code,
        pix_qr_code_base64=delivery.pix_qr_code_base64,
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

    # Phase 12: platform PIX delivery payment (corrida collected before dispatch).
    pix_payment_port = None
    if body.platform_pix:
        from app.payments.factory import get_payment_adapter

        pix_payment_port = get_payment_adapter()

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
        pix_payment_port=pix_payment_port,
    )
    await session.commit()
    # Kick off the cascade only for immediate deliveries (Phase 8 — RN-009 / D-01).
    # Scheduled (AGENDADA) → released by Inngest. PIX (AGUARDANDO_PAGAMENTO) → released
    # by the Safe2Pay webhook after payment is confirmed.
    if result.state not in ("AGENDADA", "AGUARDANDO_PAGAMENTO"):
        from app.workers.dispatch import enqueue_dispatch

        await enqueue_dispatch(result.delivery_id)
    return result


@router.get("/{delivery_id}/pix-status", response_model=dict)
async def get_delivery_pix_status(
    delivery_id: int,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> dict:
    """Poll PIX payment status for a delivery in AGUARDANDO_PAGAMENTO (Phase 12).

    Returns `paid=true` once the Safe2Pay webhook has confirmed the charge. The
    frontend polls this endpoint every few seconds until paid, then navigates to
    the delivery detail page and dispatch starts.
    """
    delivery = await service.get_delivery(
        session, area_id=scope.area_id, merchant_id=scope.merchant_id, delivery_id=delivery_id
    )
    from app.payments import repo as payments_repo

    charge = await payments_repo.get_charge_by_delivery(session, delivery_id=delivery.id)
    paid = charge is not None and charge.status == "paid"
    return {
        "paid": paid,
        "state": delivery.state,
        "qr_code": delivery.pix_qr_code,
        "qr_code_base64": delivery.pix_qr_code_base64,
    }


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


@router.post("/teams-for-address")
async def teams_for_address(
    body: dict,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> dict:
    """Geocode address → resolve zone → return eligible teams (couriers with ativo=True).

    Falls back to all teams when geocoding fails or address has no zone match.
    Couriers with no courier_zonas row inherit the team's zone price; if the TEAM
    never configured a price for this zone either, those couriers are excluded
    (a zone without preço mínimo do time não pode virar cobrança de R$0,00).
    """
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func as sa_func, select

    from app.areas.models import Area, Zona
    from app.areas.zona_finder import find_zona_id
    from app.couriers.models import Courier, CourierPricingTable, CourierZona
    from app.neighborhoods.models import Neighborhood
    from app.ratings.models import CourierRating
    from app.teams.models import Team, TeamZona

    dropoff_address: str = body.get("dropoff_address", "")
    dropoff_number: str | None = body.get("dropoff_number")
    dropoff_neighborhood_id: int | None = body.get("dropoff_neighborhood_id")
    cep: str | None = body.get("cep") or None

    # Geocode to find zone.
    zona_id: int | None = None
    zona_name: str | None = None
    if dropoff_address and dropoff_neighborhood_id is not None:
        try:
            from app.integrations.factory import get_geocoding_adapter

            area = await session.get(Area, scope.area_id)
            nbhd = await session.get(Neighborhood, dropoff_neighborhood_id)
            parts = [dropoff_address, dropoff_number, nbhd.name if nbhd else None, cep, area.name if area else None]
            address_str = ", ".join(p for p in parts if p)
            geo = await get_geocoding_adapter().geocode(address_str)
            if geo is not None:
                zona_id = await find_zona_id(session, area_id=scope.area_id, lat=geo.lat, lng=geo.lng)
                if zona_id is not None:
                    zona = await session.get(Zona, zona_id)
                    zona_name = zona.name if zona else None
        except Exception:
            pass  # geocoding unavailable — fallback to all teams

    # Online active couriers.
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

    # Filter by zone ativo (couriers with no row are treated as active).
    if zona_id is not None and couriers:
        courier_ids = [c.id for c in couriers]
        zona_inactive_ids: set[int] = {
            cz.courier_id
            for cz in (await session.execute(
                select(CourierZona).where(
                    CourierZona.zona_id == zona_id,
                    CourierZona.courier_id.in_(courier_ids),
                    CourierZona.ativo.is_(False),
                )
            )).scalars()
        }
        couriers = [c for c in couriers if c.id not in zona_inactive_ids]

    courier_ids = [c.id for c in couriers]

    # Ratings (90-day avg).
    ratings: dict[int, float] = {}
    if courier_ids:
        cutoff = datetime.now(UTC) - timedelta(days=90)
        rows = (await session.execute(
            select(CourierRating.courier_id, sa_func.avg(CourierRating.stars).label("avg"))
            .where(CourierRating.courier_id.in_(courier_ids), CourierRating.created_at >= cutoff)
            .group_by(CourierRating.courier_id)
        )).all()
        ratings = {int(r.courier_id): round(float(r.avg), 1) for r in rows}

    # Pricing: zone prices first, then old pricing table as fallback.
    pricing: dict[int, int | None] = {}
    if courier_ids and zona_id is not None:
        cz_prices: dict[int, int] = {
            cz.courier_id: cz.preco_cents
            for cz in (await session.execute(
                select(CourierZona).where(
                    CourierZona.zona_id == zona_id,
                    CourierZona.courier_id.in_(courier_ids),
                    CourierZona.ativo.is_(True),
                )
            )).scalars()
        }
        team_ids_set = {c.team_id for c in couriers if c.team_id is not None}
        tz_map: dict[int, int] = {}
        if team_ids_set:
            tz_map = {
                tz.team_id: tz.preco_minimo_cents
                for tz in (await session.execute(
                    select(TeamZona).where(TeamZona.zona_id == zona_id, TeamZona.team_id.in_(team_ids_set))
                )).scalars()
            }
        # Sem preço próprio nem preço do time para esta zona → fora da lista
        # (nunca oferecer entrega a preço 0 por omissão).
        couriers = [
            c for c in couriers
            if c.id in cz_prices or (c.team_id is not None and c.team_id in tz_map)
        ]
        courier_ids = [c.id for c in couriers]
        for c in couriers:
            if c.id in cz_prices:
                pricing[c.id] = cz_prices[c.id]
            elif c.team_id is not None and c.team_id in tz_map:
                pricing[c.id] = tz_map[c.team_id]
    if courier_ids and not pricing:
        for pr in (await session.execute(
            select(CourierPricingTable).where(
                CourierPricingTable.courier_id.in_(courier_ids),
                CourierPricingTable.area_id == scope.area_id,
            )
        )).scalars():
            if pr.courier_id not in pricing and pr.price is not None:
                pricing[pr.courier_id] = int(pr.price * 100)

    teams = list(
        (await session.execute(
            select(Team).where(Team.area_id == scope.area_id, Team.deleted_at.is_(None)).order_by(Team.id)
        )).scalars().all()
    )
    result_teams = [
        {
            "id": team.id,
            "name": team.name,
            "preco_minimo_cents": tz_map.get(team.id),
            "couriers": [
                {
                    "id": c.id,
                    "full_name": c.full_name,
                    "avg_stars": ratings.get(c.id, 0.0),
                    "price_cents": pricing.get(c.id),
                }
                for c in couriers if c.team_id == team.id
            ],
        }
        for team in teams
    ]

    # Active plan taxa — included so the frontend can show the full cost breakdown
    # (corrida + taxa_pix + taxa_servico) in the PIX confirmation modal.
    from app.merchants.models import MerchantSubscription
    from app.plans.models import SubscriptionPlan

    plan_taxa_pix_cents = 0
    plan_taxa_servico_cents = 0
    active_plan = (await session.execute(
        select(SubscriptionPlan)
        .join(MerchantSubscription, MerchantSubscription.plan_id == SubscriptionPlan.id)
        .where(
            MerchantSubscription.merchant_id == scope.merchant_id,
            MerchantSubscription.area_id == scope.area_id,
            MerchantSubscription.status == "active",
        )
    )).scalars().first()
    if active_plan is not None:
        plan_taxa_pix_cents = active_plan.taxa_pix_cents
        plan_taxa_servico_cents = active_plan.taxa_servico_cents

    return {
        "zona_id": zona_id,
        "zona_name": zona_name,
        "teams": result_teams,
        "plan_taxa_pix_cents": plan_taxa_pix_cents,
        "plan_taxa_servico_cents": plan_taxa_servico_cents,
    }


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
    courier_phone: str | None = None
    courier_vehicle_type: str | None = None
    courier_vehicle_plate: str | None = None
    courier_rating: float | None = None
    courier_rating_count = 0
    courier_total_deliveries = 0
    courier_since: str | None = None
    if delivery.courier_id is not None:
        from sqlalchemy import func as sa_func, select

        from app.couriers.models import Courier
        from app.deliveries.models import Delivery
        from app.ratings.models import CourierRating

        courier = await session.get(Courier, delivery.courier_id)
        if courier is not None:
            courier_name = courier.full_name
            courier_phone = courier.phone_e164
            courier_vehicle_type = courier.vehicle_type
            courier_vehicle_plate = courier.vehicle_plate
            courier_since = courier.created_at.isoformat() if courier.created_at else None
        rating_row = (
            await session.execute(
                select(
                    sa_func.avg(CourierRating.stars),
                    sa_func.count(CourierRating.id),
                ).where(CourierRating.courier_id == delivery.courier_id)
            )
        ).one()
        if rating_row[0] is not None:
            courier_rating = round(float(rating_row[0]), 1)
        courier_rating_count = int(rating_row[1] or 0)
        courier_total_deliveries = int(
            (
                await session.execute(
                    select(sa_func.count(Delivery.id)).where(
                        Delivery.courier_id == delivery.courier_id,
                        Delivery.state == "FINALIZADA",
                    )
                )
            ).scalar_one()
        )
    # Fetch neighborhood name for display.
    neighborhood_name: str | None = None
    from app.neighborhoods.models import Neighborhood
    nbhd = await session.get(Neighborhood, delivery.dropoff_neighborhood_id)
    if nbhd is not None:
        neighborhood_name = nbhd.name
    # Fetch team names from the delivery's team_ids JSON array.
    team_names: list[str] = []
    if delivery.team_ids:
        from app.teams.models import Team
        from sqlalchemy import select
        rows = (await session.execute(
            select(Team.name).where(Team.id.in_(delivery.team_ids))
        )).scalars().all()
        team_names = list(rows)
    return _delivery_out(
        delivery, recipient,
        courier_name=courier_name,
        neighborhood_name=neighborhood_name,
        team_names=team_names,
        courier_phone=courier_phone,
        courier_vehicle_type=courier_vehicle_type,
        courier_vehicle_plate=courier_vehicle_plate,
        courier_rating=courier_rating,
        courier_rating_count=courier_rating_count,
        courier_total_deliveries=courier_total_deliveries,
        courier_since=courier_since,
    )


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
    # Estorno do PIX (se pago via platform_pix), qualquer estado cancelável
    # (CORRECAO-249 — o custo RN-004 nunca virou cobrança real, então reter o
    # estorno pra "não brigar" com ele só deixava o dinheiro preso). Enfileirado
    # (externo, Safe2Pay — não síncrono do lado deles); nunca bloqueia a
    # resposta do cancelamento.
    from app.workers.refund import enqueue_refund

    await enqueue_refund(delivery.id)
    recipient = None
    if delivery.recipient_id is not None:
        from app.deliveries.models import Recipient

        recipient = await session.get(Recipient, delivery.recipient_id)
    return _delivery_out(delivery, recipient)


__all__ = ["router", "RateLimitedError"]
