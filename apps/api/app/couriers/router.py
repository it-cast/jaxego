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

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.auth.principals import Actor
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
    CourierAdminDetailOut,
    CourierAdminListItem,
    CourierAdminListOut,
    CourierDocumentAdminItem,
    CourierDocumentItem,
    CourierLocationBody,
    CourierProfileOut,
    CourierSignupBody,
    CourierSignupResponse,
    CoverageBody,
    CoverageRowRead,
    DocumentPresignBody,
    DocumentPresignResponse,
    DocumentReadResponse,
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
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.deliveries.schemas import (
    CourierDeliveryListItem,
    CourierDeliveryListOut,
    CourierDeliveryOut,
    mask_phone_display,
)
from app.areas.config_schema import AreaConfig
from app.areas.models import Area
from app.integrations.factory import get_receita_adapter, get_storage_adapter

router = APIRouter(prefix="/couriers", tags=["couriers"])
admin_router = APIRouter(prefix="/admin/couriers", tags=["couriers-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# ---------------------------------------------------------------------------
# Public + authenticated courier flow
# ---------------------------------------------------------------------------
@router.get("/teams")
async def list_teams_public(
    area_id: int,
    session: SessionDep,
) -> dict:
    """Public list of teams for a given area (courier signup)."""
    from app.teams.service import list_teams
    teams, total = await list_teams(session, area_id=area_id)
    return {"items": [{"id": t.id, "name": t.name} for t in teams]}


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
    session: AsyncSession, *, courier_id: int, user: Actor, scope: int | None
) -> Courier:
    # Pós-users: o ator courier É a linha de couriers — self-only = mesmo id.
    if user.type != "courier" or user.id != courier_id:
        raise NotFoundError("Entregador não encontrado.")
    stmt = select(Courier).where(Courier.id == courier_id)
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


# ---------------------------------------------------------------------------
# Zonas e preços — entregador define preço por zona (override do team_zona).
# ---------------------------------------------------------------------------

@router.get("/{courier_id}/zonas")
async def list_courier_zonas(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[dict]:
    """Zonas da área com cobertura (ativo), preço da equipe e override do entregador."""
    from app.areas.models import Zona
    from app.couriers.models import CourierZona
    from app.teams.models import TeamZona

    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    zonas = list(
        (await session.execute(
            select(Zona).where(Zona.area_id == courier.area_id).order_by(Zona.id)
        )).scalars().all()
    )
    # Team default prices
    team_prices: dict[int, int] = {}
    if courier.team_id:
        for tz in (await session.execute(
            select(TeamZona).where(TeamZona.team_id == courier.team_id)
        )).scalars().all():
            team_prices[tz.zona_id] = tz.preco_minimo_cents
    # Courier zona rows (coverage + price override)
    courier_zonas: dict[int, CourierZona] = {}
    for cz in (await session.execute(
        select(CourierZona).where(CourierZona.courier_id == courier.id)
    )).scalars().all():
        courier_zonas[cz.zona_id] = cz

    return [
        {
            "zona_id": z.id,
            "zona_nome": z.name,
            "boundary": z.boundary,
            # Sem override do entregador: só está ativo se a equipe configurou
            # preço mínimo para a zona (mesma regra do despacho — cascade.py).
            "ativo": (
                courier_zonas[z.id].ativo
                if z.id in courier_zonas
                else z.id in team_prices
            ),
            "team_preco_cents": team_prices.get(z.id),
            "courier_preco_cents": courier_zonas[z.id].preco_cents if z.id in courier_zonas else None,
        }
        for z in zonas
    ]


@router.patch("/{courier_id}/zonas/{zona_id}")
async def patch_courier_zona(
    courier_id: int,
    zona_id: int,
    body: dict,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    """Atualiza cobertura (ativo) e/ou preço do entregador para uma zona."""
    from app.areas.models import Zona
    from app.couriers.models import CourierZona
    from fastapi import HTTPException

    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    zona = await session.get(Zona, zona_id)
    if zona is None or zona.area_id != courier.area_id:
        raise HTTPException(status_code=404, detail="Zona não encontrada.")
    existing = (await session.execute(
        select(CourierZona).where(
            CourierZona.courier_id == courier.id,
            CourierZona.zona_id == zona_id,
        )
    )).scalar_one_or_none()
    if existing is None:
        existing = CourierZona(
            courier_id=courier.id,
            zona_id=zona_id,
            area_id=courier.area_id,
            ativo=True,
            preco_cents=0,
        )
        session.add(existing)
        await session.flush()
    if "ativo" in body:
        existing.ativo = bool(body["ativo"])
    if "preco_cents" in body:
        existing.preco_cents = int(body["preco_cents"])
    await session.commit()
    return {"zona_id": zona_id, "ativo": existing.ativo, "preco_cents": existing.preco_cents}


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
        session,
        area_id=courier.area_id,
        courier_id=courier.id,
        online=body.online,
        online_until=body.online_until,
    )
    await session.commit()
    # busy is DERIVED; the real active-delivery count arrives in Phase 7/8 (0 here).
    raw_cfg = {}
    area_obj = await session.get(Area, updated.area_id)
    if area_obj and area_obj.config:
        raw_cfg = dict(area_obj.config)
    area_cfg = AreaConfig(**raw_cfg)
    busy = availability_svc.compute_busy(active_deliveries=0, max_concurrent=area_cfg.max_entregas_simultaneas)
    return AvailabilityResponse(is_online=updated.is_online, busy=busy, online_until=updated.online_until)


@router.patch("/{courier_id}/location", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def update_location(
    courier_id: int,
    body: CourierLocationBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> Response:
    """Record courier's current position while online (dispatch proximity ranking).

    Only accepted when the courier is online; silently ignored if offline to avoid
    stale positions skewing the ranking after the courier goes idle.
    """
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    if courier.is_online:
        courier.lat = body.lat
        courier.lng = body.lng
        courier.location_at = datetime.now(UTC)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Courier-facing delivery reads (F1.0 / MR-1). Self-only via _own_courier
# (IDOR → 404). PII reveal-by-state (RN-013): full dropoff + recipient only
# AFTER pickup (COLETADA+). `/active` is declared before `/{delivery_id}`.
# ---------------------------------------------------------------------------
_COURIER_DROPOFF_REVEALED = frozenset({"COLETADA", "ENTREGUE", "RECUSADA_NO_DESTINO", "FINALIZADA"})


def _courier_delivery_out(delivery, recipient, *, merchant_trade_name: str | None = None, dropoff_neighborhood_name: str | None = None) -> CourierDeliveryOut:
    """Serialize a delivery for the assigned courier, hiding destination PII
    until pickup (RN-013). The recipient phone is masked even when revealed."""
    return CourierDeliveryOut(
        id=delivery.id,
        public_token=delivery.public_token,
        state=delivery.state,
        payment_method=delivery.payment_method,
        proof_method=delivery.proof_method,
        merchant_trade_name=merchant_trade_name,
        pickup_address=delivery.pickup_address,
        pickup_neighborhood=delivery.pickup_neighborhood,
        pickup_lat=delivery.pickup_lat,
        pickup_lng=delivery.pickup_lng,
        dropoff_neighborhood_id=delivery.dropoff_neighborhood_id,
        dropoff_neighborhood_name=dropoff_neighborhood_name,
        distance_m=delivery.distance_m,
        dropoff_address=delivery.dropoff_address,
        dropoff_number=delivery.dropoff_number,
        dropoff_complement=delivery.dropoff_complement,
        dropoff_reference=delivery.dropoff_reference,
        dropoff_lat=delivery.dropoff_lat,
        dropoff_lng=delivery.dropoff_lng,
        recipient_name=recipient.name if recipient else None,
        recipient_phone_masked=mask_phone_display(recipient.phone_e164) if recipient else None,
        recipient_phone=recipient.phone_e164 if recipient else None,
        price_cents=delivery.price_cents,
        fee_cents=delivery.fee_cents,
        has_image=delivery.image_key is not None,
        reference_number=delivery.reference_number,
        items_description=delivery.items_description,
        items_quantity=delivery.items_quantity,
        weight_g=delivery.weight_g,
        length_cm=delivery.length_cm,
        width_cm=delivery.width_cm,
        height_cm=delivery.height_cm,
        courier_collection_method=delivery.courier_collection_method,
        receipt_method=delivery.receipt_method,
        notes=delivery.notes,
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
    delivery, recipient = result
    merchant = await session.get(Merchant, delivery.merchant_id)
    nbhd = await session.get(Neighborhood, delivery.dropoff_neighborhood_id)
    return _courier_delivery_out(delivery, recipient, merchant_trade_name=merchant.trade_name if merchant else None, dropoff_neighborhood_name=nbhd.name if nbhd else None)


@router.get("/{courier_id}/deliveries/active-list", response_model=list[CourierDeliveryOut])
async def list_active_deliveries(
    courier_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[CourierDeliveryOut]:
    """All of the courier's in-progress deliveries (ACEITA/COLETADA), newest first."""
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    results = await delivery_service.get_courier_active_deliveries(session, courier_id=courier.id)
    out: list[CourierDeliveryOut] = []
    for delivery, recipient in results:
        merchant = await session.get(Merchant, delivery.merchant_id)
        nbhd = await session.get(Neighborhood, delivery.dropoff_neighborhood_id)
        out.append(_courier_delivery_out(
            delivery, recipient,
            merchant_trade_name=merchant.trade_name if merchant else None,
            dropoff_neighborhood_name=nbhd.name if nbhd else None,
        ))
    return out


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
            pickup_address=d.pickup_address,
            dropoff_address=d.dropoff_address,
            dropoff_number=d.dropoff_number,
            dropoff_neighborhood_id=d.dropoff_neighborhood_id,
            distance_m=d.distance_m,
            price_cents=d.price_cents,
            fee_cents=d.fee_cents,
            has_image=d.image_key is not None,
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
    merchant = await session.get(Merchant, delivery.merchant_id)
    nbhd = await session.get(Neighborhood, delivery.dropoff_neighborhood_id)
    return _courier_delivery_out(delivery, recipient, merchant_trade_name=merchant.trade_name if merchant else None, dropoff_neighborhood_name=nbhd.name if nbhd else None)


@router.get("/{courier_id}/deliveries/{delivery_id}/image")
async def get_courier_delivery_image(
    courier_id: int,
    delivery_id: int,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    """Presigned GET for the delivery product image (courier-facing)."""
    from app.integrations.factory import get_storage_adapter
    from fastapi import HTTPException
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    delivery, _ = await delivery_service.get_courier_delivery(session, courier_id=courier.id, delivery_id=delivery_id)
    if not delivery.image_key:
        raise HTTPException(status_code=404, detail="Sem imagem.")
    storage = get_storage_adapter()
    presign = await storage.presign_get(delivery.image_key, expires_in=180)
    return {"url": presign.url, "expires_in": 180}


@router.post("/{courier_id}/deliveries/{delivery_id}/arrived")
async def mark_arrived(
    courier_id: int,
    delivery_id: int,
    body: CourierLocationBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    """Log 'chegou ao destino' — audit only, no state transition (RN-005:
    states advance via proofs, not this tap). CORRECAO-252."""
    from app.tracking.service import ACTION_CHEGOU_DESTINO, log_courier_action

    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    delivery, _ = await delivery_service.get_courier_delivery(
        session, courier_id=courier.id, delivery_id=delivery_id
    )
    await log_courier_action(
        session,
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        courier_id=courier.id,
        action=ACTION_CHEGOU_DESTINO,
        lat=body.lat,
        lng=body.lng,
    )
    await session.commit()
    return {"ok": True}


@router.post("/{courier_id}/deliveries/{delivery_id}/collect")
async def mark_collected(
    courier_id: int,
    delivery_id: int,
    body: CourierLocationBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    """Mark a delivery as collected (ACEITA → COLETADA) without photo proof."""
    from app.deliveries.service import transition
    from app.tracking.service import ACTION_COLETOU, log_courier_action

    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    delivery, _ = await delivery_service.get_courier_delivery(
        session, courier_id=courier.id, delivery_id=delivery_id
    )
    await transition(session, delivery=delivery, to_state="COLETADA", actor_id=user.id, actor_type="courier", ip=None)
    await log_courier_action(
        session,
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        courier_id=courier.id,
        action=ACTION_COLETOU,
        lat=body.lat,
        lng=body.lng,
    )
    await session.commit()
    return {"ok": True, "state": "COLETADA"}


@router.post("/{courier_id}/deliveries/{delivery_id}/cancel-acceptance")
async def cancel_acceptance(
    courier_id: int,
    delivery_id: int,
    body: CourierLocationBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    """Entregador desiste depois de aceitar, antes de coletar (CORRECAO-262).

    ACEITA → CRIADA — reabre a entrega pra fila de despacho, excluído da nova
    rodada. Só é possível entre o aceite e a coleta (422 depois de COLETADA).
    """
    from app.deliveries.service import courier_cancel_acceptance
    from app.tracking.service import ACTION_CANCELOU_ACEITE, log_courier_action

    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    delivery = await courier_cancel_acceptance(
        session,
        delivery_id=delivery_id,
        courier_id=courier.id,
        reason="courier_desistiu_pre_coleta",
        gps=(body.lat, body.lng),
        ip=None,
    )
    await log_courier_action(
        session,
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        courier_id=courier.id,
        action=ACTION_CANCELOU_ACEITE,
        lat=body.lat,
        lng=body.lng,
    )
    await session.commit()

    # Reabre a fila — efeito em Redis/fila, nunca dentro da transação do banco
    # (mesmo padrão de enqueue_payout/enqueue_refund). Best-effort: uma falha
    # aqui não desfaz o cancelamento já persistido; a entrega fica CRIADA e o
    # sweep `redispatch_stale_deliveries` (cron) recupera em até 5 min.
    from app.core.redis import get_redis_client
    from app.dispatch import offer_state
    from app.workers.dispatch import enqueue_dispatch

    r = get_redis_client()
    await offer_state.add_declined(r, delivery.id, courier.id)
    await enqueue_dispatch(delivery.id)

    return {"ok": True, "state": delivery.state}


@router.post("/{courier_id}/deliveries/{delivery_id}/finalize-no-proof")
async def finalize_no_proof(
    courier_id: int,
    delivery_id: int,
    body: CourierLocationBody,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    """Finalize a delivery without proof (proof_method=none): COLETADA → ENTREGUE → FINALIZADA."""
    from app.deliveries.service import transition
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    delivery, _ = await delivery_service.get_courier_delivery(
        session, courier_id=courier.id, delivery_id=delivery_id
    )
    if delivery.proof_method != "none":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Esta entrega exige comprovação.")
    await transition(session, delivery=delivery, to_state="ENTREGUE", actor_id=user.id, actor_type="courier", ip=None)
    await transition(session, delivery=delivery, to_state="FINALIZADA", actor_id=user.id, actor_type="courier", ip=None)

    from app.tracking.service import ACTION_ENTREGOU, log_courier_action
    await log_courier_action(
        session,
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        courier_id=courier.id,
        action=ACTION_ENTREGOU,
        lat=body.lat,
        lng=body.lng,
    )

    from app.merchants.credit import reconcile_delivery_credit
    await reconcile_delivery_credit(session, delivery=delivery)

    await session.commit()

    from app.workers.payout import enqueue_payout
    await enqueue_payout(delivery.id)

    return {"ok": True, "state": "FINALIZADA"}


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
    team_name = None
    if courier.team_id:
        from app.teams.models import Team
        team = await session.get(Team, courier.team_id)
        team_name = team.name if team else None
    return CourierProfileOut(
        id=courier.id,
        full_name=courier.full_name,
        cpf_masked=mask_cpf_display(courier.cpf or ''),
        phone_masked=mask_phone(courier.phone_e164),
        email_masked=mask_email(courier.email),
        vehicle_type=courier.vehicle_type,
        vehicle_plate=courier.vehicle_plate,
        kyc_level=courier.kyc_level,
        status=courier.status,
        is_online=courier.is_online,
        online_until=courier.online_until,
        mei_pending=courier.mei_pending,
        team_id=courier.team_id,
        team_name=team_name,
        documents=[
            CourierDocumentItem(
                id=d.id, kind=d.kind, status=d.status,
                reject_reason=d.reject_reason, reject_detail=d.reject_detail,
            ) for d in docs
        ],
    )


@router.patch("/{courier_id}/profile")
async def update_courier_profile(
    courier_id: int,
    body: dict,
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> dict:
    courier = await _own_courier(session, courier_id=courier_id, user=user, scope=scope)
    if "full_name" in body and body["full_name"]:
        courier.full_name = body["full_name"]
    # team_id não é auto-editável (bloqueado a pedido do usuário) — só é
    # definido no cadastro; mudança de equipe fica reservada pra admin.
    if "password" in body and body["password"]:
        from app.core.security import hash_password, verify_password
        current = body.get("current_password", "")
        ok, _ = verify_password(courier.password_hash or "", current)
        if not ok:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Senha atual incorreta")
        courier.password_hash = hash_password(body["password"])
    await session.flush()
    await session.commit()
    return {"ok": True}


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
            cpf_masked=mask_cpf_display(cpf or ''),
            status=c.status,
            kyc_level=c.kyc_level,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c, cpf in rows
    ]
    return CourierAdminListOut(
        items=items, total=total, limit=min(limit, 100), offset=max(offset, 0)
    )


@admin_router.get("/{courier_id}", response_model=CourierAdminDetailOut)
async def get_area_courier(
    courier_id: int,
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
) -> CourierAdminDetailOut:
    """Courier detail + documents for the KYC review page. Area-scoped (TH-09)."""
    from app.couriers.models import Courier, CourierDocument

    query = select(Courier).where(Courier.id == courier_id)
    if scope is not None:
        query = query.where(Courier.area_id == scope)
    courier = (await session.execute(query)).scalar_one_or_none()
    if courier is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Entregador não encontrado.")
    user_cpf = courier.cpf
    docs = (
        await session.execute(
            select(CourierDocument)
            .where(CourierDocument.courier_id == courier.id)
            .order_by(CourierDocument.id)
        )
    ).scalars().all()
    return CourierAdminDetailOut(
        id=courier.id,
        full_name=courier.full_name,
        cpf_masked=mask_cpf_display(user_cpf or ''),
        status=courier.status,
        kyc_level=courier.kyc_level,
        vehicle_type=courier.vehicle_type,
        vehicle_plate=courier.vehicle_plate,
        created_at=courier.created_at.isoformat() if courier.created_at else None,
        documents=[
            CourierDocumentAdminItem(
                id=d.id,
                kind=d.kind,
                status=d.status,
                reject_reason=d.reject_reason,
                reject_detail=d.reject_detail,
                created_at=d.created_at.isoformat() if d.created_at else None,
            )
            for d in docs
        ],
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


# A aprovação/reprovação de documentos (KYC) é feita pelo admin da EQUIPE em
# /v1/team-admin/couriers/{id}/documents/{doc_id}/approve|reject — não há mais
# review pelo admin da cidade.
