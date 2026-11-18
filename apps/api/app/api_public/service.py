"""Public create-delivery orchestration (F-04) — auth+idempotency over the SAME service.

The flow (D-04 / TH-04):
  1. canonicalise the request body → SHA-256 `request_hash`
  2. lock the `(api_key_id, idempotency_key)` snapshot FOR UPDATE
     - exists + same hash → return the cached response (replay, no second create)
     - exists + different hash → 409 (key reuse with a different body)
  3. resolve the target store WITHIN the key's area (404 cross-area — TH-03)
  4. call `deliveries.service.create_delivery` (the SAME state machine)
  5. persist the 24h response snapshot, return the response

The store is NEVER resolved outside the key's `area_id` (IDOR closed by the WHERE).
PII (recipient phone/address) is NEVER logged (TH-09).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime, timedelta

from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys import repo as key_repo
from app.api_keys.models import ApiIdempotencyKey
from app.api_public.schemas import (
    PublicCourierOut,
    PublicCreateDeliveryBody,
    PublicCreateMerchantBody,
    PublicCreateMerchantOut,
    PublicMerchantAccessOut,
    PublicDeliveryDetail,
    PublicDeliveryResponse,
    PublicMerchantOut,
    PublicPoint,
    PublicQuoteOut,
    PublicTimelineItem,
)
from app.core.exceptions import AppError, NotFoundError
from app.deliveries import service as delivery_service
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.deliveries.schemas import CreateDeliveryBody
from app.deliveries.state_machine import DELIVERY_TRANSITIONS
from app.merchants.models import Merchant, MerchantSubscription
from app.neighborhoods.models import Neighborhood

# Idempotency snapshot lifetime (ADR-010 / D-04).
IDEMPOTENCY_TTL = timedelta(hours=24)


class IdempotencyConflictError(AppError):
    """Same Idempotency-Key, different request body (D-04 → 409)."""

    status_code = 409
    code = "idempotency_key_conflict"

    def __init__(self) -> None:
        super().__init__("Idempotency-Key já usada com um corpo de requisição diferente.")


class StoreNotResolvableError(AppError):
    """No store in the key's area matches the target (D-03 → 404, no existence leak)."""

    status_code = 404
    code = "merchant_not_found"

    def __init__(self) -> None:
        super().__init__("Loja não encontrada para esta chave de API.")


class NeighborhoodNotFoundError(AppError):
    """O bairro de destino não está no catálogo da área (422 — o integrador corrige o endereço)."""

    status_code = 422
    code = "neighborhood_not_found"

    def __init__(self, nome: str | None = None) -> None:
        texto = (
            f'O bairro "{nome}" não está na área atendida.'
            if nome
            else "Bairro de destino fora da área atendida."
        )
        super().__init__(texto)


class _PublicInternalBody(CreateDeliveryBody):
    """Corpo interno da criação pela API pública.

    - `team_ids` opcional: a API pública não escolhe equipe; vazio = todos os entregadores
      da área elegíveis (o despacho trata `not team_ids` como "qualquer equipe").
    - coordenadas da coleta/entrega: `create_delivery` lê com getattr e usa na zona.
    """

    team_ids: list[int] | None = None  # type: ignore[assignment]
    pickup_lat: float | None = Field(default=None, ge=-90, le=90)
    pickup_lng: float | None = Field(default=None, ge=-180, le=180)
    dropoff_lat: float | None = Field(default=None, ge=-90, le=90)
    dropoff_lng: float | None = Field(default=None, ge=-180, le=180)


def normalizar_nome(nome: str | None) -> str:
    """Bairro sem acento, sem caixa e com espaços simples ("São  Félix" → "sao felix")."""
    texto = unicodedata.normalize("NFKD", str(nome or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().casefold()


def so_digitos(texto: str | None) -> str:
    return re.sub(r"\D", "", str(texto or ""))


def tracking_url(public_token: str | None) -> str | None:
    """`<PUBLIC_WEB_BASE_URL>/r/<token>`; None sem a base configurada."""
    from app.core.config import get_settings

    base = (get_settings().public_web_base_url or "").strip().rstrip("/")
    if not base or not public_token:
        return None
    return f"{base}/r/{public_token}"


async def resolve_neighborhood(
    session: AsyncSession, *, area_id: int, nbhd_id: int | None, nome: str | None
) -> Neighborhood:
    """Bairro do catálogo DA ÁREA (id ou nome normalizado). Arquivado não vale."""
    stmt = select(Neighborhood).where(
        Neighborhood.area_id == area_id, Neighborhood.archived_at.is_(None)
    )
    if nbhd_id is not None:
        nbhd = (await session.execute(stmt.where(Neighborhood.id == nbhd_id))).scalars().first()
        if nbhd is None:
            raise NeighborhoodNotFoundError()
        return nbhd
    alvo = normalizar_nome(nome)
    if not alvo:
        raise NeighborhoodNotFoundError()
    candidatos = [
        n for n in (await session.execute(stmt)).scalars().all() if normalizar_nome(n.name) == alvo
    ]
    if not candidatos:
        raise NeighborhoodNotFoundError(nome)
    # Mesmo nome duas vezes no catálogo: o formal ganha do informal, depois o mais antigo
    candidatos.sort(key=lambda n: (bool(getattr(n, "is_informal", False)), n.id))
    return candidatos[0]


def canonical_request_hash(body: PublicCreateDeliveryBody) -> str:
    """SHA-256 (hex) of the canonical JSON body — distinguishes replay from reuse."""
    canonical = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def _resolve_merchant(
    session: AsyncSession, *, area_id: int, body: PublicCreateDeliveryBody
) -> Merchant:
    """Resolve the target store WITHIN the key's area (404 cross-area — TH-03)."""
    stmt = select(Merchant).where(Merchant.area_id == area_id)
    if body.merchant_external_ref is not None:
        stmt = stmt.where(Merchant.external_ref == body.merchant_external_ref)
    else:
        stmt = stmt.where(Merchant.id == body.merchant_id)
    merchant = (await session.execute(stmt)).scalars().first()
    if merchant is None:
        raise StoreNotResolvableError()
    return merchant


def _to_internal_body(
    body: PublicCreateDeliveryBody, *, dropoff_neighborhood_id: int
) -> CreateDeliveryBody:
    """Map the public body onto the internal create contract (drops store-target fields)."""
    return _PublicInternalBody(
        pickup_address=body.pickup_address,
        pickup_neighborhood=body.pickup_neighborhood,
        pickup_lat=body.pickup_lat,
        pickup_lng=body.pickup_lng,
        dropoff_neighborhood_id=dropoff_neighborhood_id,
        dropoff_address=body.dropoff_address,
        dropoff_number=body.dropoff_number,
        dropoff_complement=body.dropoff_complement,
        dropoff_reference=body.dropoff_reference,
        cep=so_digitos(body.cep)[:8] or None,
        dropoff_lat=body.dropoff_lat,
        dropoff_lng=body.dropoff_lng,
        distance_m=body.distance_m,
        recipient_name=body.recipient_name,
        recipient_phone_e164=body.recipient_phone_e164,
        recipient_email=body.recipient_email,
        recipient_cpf=body.recipient_cpf,
        items_description=body.items_description,
        items_quantity=body.items_quantity,
        declared_value_cents=body.declared_value_cents,
        reference_number=body.reference_number,
        notes=body.notes,
        proof_method=body.proof_method,
        payment_method=body.payment_method,
        team_ids=None,
    )


async def create_public_delivery(
    session: AsyncSession,
    *,
    area_id: int,
    api_key_id: int,
    idempotency_key: str,
    body: PublicCreateDeliveryBody,
    ip: str | None,
) -> tuple[int, PublicDeliveryResponse, bool]:
    """Create (or replay) a delivery. Returns (status_code, response, replayed)."""
    request_hash = canonical_request_hash(body)

    # Replay guard: lock the snapshot row for this (key, idempotency_key).
    existing = await key_repo.get_idempotency_locked(
        session, api_key_id=api_key_id, idempotency_key=idempotency_key
    )
    if existing is not None:
        if existing.request_hash != request_hash:
            raise IdempotencyConflictError()
        cached = PublicDeliveryResponse.model_validate(json.loads(existing.response_body))
        return existing.response_status, cached, True

    merchant = await _resolve_merchant(session, area_id=area_id, body=body)
    nbhd = await resolve_neighborhood(
        session,
        area_id=area_id,
        nbhd_id=body.dropoff_neighborhood_id,
        nome=body.dropoff_neighborhood_name,
    )

    result = await delivery_service.create_delivery(
        session,
        area_id=area_id,
        merchant_id=merchant.id,
        actor_user_id=None,  # the integrator is the actor; no platform user
        body=_to_internal_body(body, dropoff_neighborhood_id=nbhd.id),
        ip=ip,
    )
    response = PublicDeliveryResponse(
        delivery_id=result.delivery_id,
        public_token=result.public_token,
        tracking_url=tracking_url(result.public_token),
        state=result.state,
        price_cents=result.price_cents,
        fee_cents=result.fee_cents,
        no_couriers_warning=result.no_couriers_warning,
    )

    snapshot = ApiIdempotencyKey(
        area_id=area_id,
        api_key_id=api_key_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_status=201,
        response_body=response.model_dump_json(),
        delivery_id=result.delivery_id,
        expires_at=datetime.now(UTC) + IDEMPOTENCY_TTL,
    )
    session.add(snapshot)
    await session.flush()
    return 201, response, False


# ---------------------------------------------------------------------------
# Vínculo da loja (Menu Certo): CNPJ/CPF → loja da área da chave.
# ---------------------------------------------------------------------------
async def resolve_merchant_by_document(
    session: AsyncSession, *, area_id: int, document: str
) -> PublicMerchantOut:
    """Loja da área com esse documento (comparado só pelos dígitos). Fora da área = 404."""
    doc = so_digitos(document)
    if len(doc) not in (11, 14):
        raise StoreNotResolvableError()
    candidatos = (
        (
            await session.execute(
                select(Merchant).where(Merchant.area_id == area_id).order_by(Merchant.id)
            )
        )
        .scalars()
        .all()
    )
    merchant = next((m for m in candidatos if so_digitos(m.document) == doc), None)
    if merchant is None:
        raise StoreNotResolvableError()
    status = merchant.status if getattr(merchant, "is_active", True) else "inactive"
    sub = await _assinatura(session, area_id=area_id, merchant_id=merchant.id)
    return PublicMerchantOut(
        merchant_id=merchant.id,
        trade_name=merchant.trade_name,
        status=status,
        external_ref=merchant.external_ref,
        access=_acesso(sub),
    )


# ---------------------------------------------------------------------------
# Cadastro da loja pelo integrador e acesso (escopo merchants:write).
# O integrador (Menu Certo) cobra a loja na própria mensalidade: a assinatura nasce no
# plano pedido, billing_status active e SEM forma de pagamento — os jobs de cobrança só
# olham card/pix e a inadimplência só existe com cobrança aberta, então nada é cobrado
# nem bloqueado aqui. Desligar = billing_status "cancelado" (a guarda de criação de
# entrega barra; o sync de inadimplência não mexe em "cancelado"). Religar = "active".
# ---------------------------------------------------------------------------
class PlanNotFoundError(AppError):
    status_code = 422
    code = "plan_not_found"

    def __init__(self) -> None:
        super().__init__("Plano não encontrado no catálogo.")


def _acesso(sub: MerchantSubscription | None) -> str:
    return "disabled" if sub is not None and sub.billing_status in ("blocked", "cancelado") else "active"


async def _assinatura(
    session: AsyncSession, *, area_id: int, merchant_id: int
) -> MerchantSubscription | None:
    return (
        await session.execute(
            select(MerchantSubscription)
            .where(
                MerchantSubscription.area_id == area_id,
                MerchantSubscription.merchant_id == merchant_id,
            )
            .order_by(MerchantSubscription.id.desc())
        )
    ).scalars().first()


async def create_merchant_by_integrator(
    session: AsyncSession,
    *,
    area_id: int,
    body: PublicCreateMerchantBody,
    receita: object,
    geocoding: object,
    ip: str | None,
    api_key_id: int,
) -> PublicCreateMerchantOut:
    """Cria a loja na área da chave pelo MESMO cadastro da tela (validação, unicidade,
    Receita, geocodificação), já ativa e no plano pago pelo integrador."""
    from app.audit.service import write_audit
    from app.merchants import service as merchant_service
    from app.merchants.schemas import MerchantSignupBody
    from app.plans import service as plans_service

    plano = await plans_service.get_plan_by_code(session, body.plan_code)
    if plano is None:
        raise PlanNotFoundError()

    resultado = await merchant_service.signup(
        session,
        body=MerchantSignupBody(
            area_id=area_id,
            account_type=body.account_type,
            document=body.document,
            trade_name=body.trade_name,
            category=body.category,
            phone_e164=body.phone_e164,
            email=body.email,
            password=body.password,
            consent=True,
            address=body.address,
            address_number=body.address_number,
            address_neighborhood=body.address_neighborhood,
            address_zip=body.address_zip,
            address_state=body.address_state,
            lat=body.lat,
            lng=body.lng,
        ),
        receita=receita,  # type: ignore[arg-type]
        geocoding=geocoding,  # type: ignore[arg-type]
        ip=ip,
    )
    merchant = await session.get(Merchant, resultado.merchant_id)
    assert merchant is not None
    # O integrador já conferiu a loja: sem Receita no ar ela não fica esperando revalidação
    if merchant.status == "pending_validation":
        merchant.status = "active"
        merchant.next_revalidation_at = None
    ref = (body.external_ref or "").strip() or None
    if ref:
        em_uso = (
            await session.execute(
                select(Merchant.id).where(Merchant.area_id == area_id, Merchant.external_ref == ref)
            )
        ).first()
        if em_uso is None:
            merchant.external_ref = ref

    sub = await _assinatura(session, area_id=area_id, merchant_id=merchant.id)
    if sub is None:
        sub = MerchantSubscription(area_id=area_id, merchant_id=merchant.id, plan_id=plano.id)
        session.add(sub)
    sub.plan_id = plano.id
    sub.status = "active"
    sub.billing_status = "active"
    sub.payment_method = None
    sub.cycle = None
    sub.amount_cents = 0
    sub.due_at = None
    await session.flush()

    await write_audit(
        session,
        actor_id=None,
        action="merchant.created_by_integrator",
        area_id=area_id,
        after={
            "merchant_id": merchant.id,
            "status": merchant.status,
            "plan": plano.code,
            "api_key_id": api_key_id,
            "consent": True,
        },
        ip=ip,
    )
    return PublicCreateMerchantOut(
        merchant_id=merchant.id,
        trade_name=merchant.trade_name,
        status=merchant.status,
        plan_code=plano.code,
        access="active",
    )


async def set_merchant_access(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    active: bool,
    ip: str | None,
    api_key_id: int,
) -> PublicMerchantAccessOut:
    """Liga/desliga a loja da área (fora da área = 404). Entregas em andamento seguem."""
    from app.audit.service import write_audit

    merchant = (
        await session.execute(
            select(Merchant).where(Merchant.id == merchant_id, Merchant.area_id == area_id)
        )
    ).scalar_one_or_none()
    if merchant is None:
        raise StoreNotResolvableError()
    sub = await _assinatura(session, area_id=area_id, merchant_id=merchant.id)
    if sub is None:
        raise AppError("A loja não tem assinatura.", code="subscription_missing")
    antes = sub.billing_status
    sub.billing_status = "active" if active else "cancelado"
    await session.flush()
    if antes != sub.billing_status:
        await write_audit(
            session,
            actor_id=None,
            action="merchant.access_by_integrator",
            area_id=area_id,
            before={"merchant_id": merchant.id, "billing_status": antes},
            after={"merchant_id": merchant.id, "billing_status": sub.billing_status, "api_key_id": api_key_id},
            ip=ip,
        )
    return PublicMerchantAccessOut(
        merchant_id=merchant.id, access=_acesso(sub), billing_status=sub.billing_status
    )


# ---------------------------------------------------------------------------
# Cotação: quantos entregadores atendem agora o destino e a faixa de preço.
# Mesma regra do `teams-for-address` da loja (preço da zona do entregador, senão o do
# time; sem preço nenhum o entregador fica de fora; sem zona, a tabela antiga).
# ---------------------------------------------------------------------------
async def _zona_do_destino(
    session: AsyncSession,
    *,
    area_id: int,
    nbhd: Neighborhood,
    lat: float | None,
    lng: float | None,
    address: str | None,
    number: str | None,
    cep: str | None,
) -> tuple[int | None, str | None]:
    from app.areas.models import Area, Zona
    from app.areas.zona_finder import find_zona_id

    if lat is None or lng is None:
        if not address:
            return None, None
        try:
            from app.integrations.factory import get_geocoding_adapter

            area = await session.get(Area, area_id)
            partes = [address, number, nbhd.name, cep, area.name if area else None]
            geo = await get_geocoding_adapter().geocode(", ".join(p for p in partes if p))
        except Exception:  # noqa: BLE001 — sem geocoding a cotação cai na tabela antiga
            geo = None
        if geo is None:
            return None, None
        lat, lng = geo.lat, geo.lng
    zona_id = await find_zona_id(session, area_id=area_id, lat=lat, lng=lng)
    if zona_id is None:
        return None, None
    zona = await session.get(Zona, zona_id)
    return zona_id, (zona.name if zona else None)


async def quote(
    session: AsyncSession,
    *,
    area_id: int,
    nbhd_id: int | None,
    nbhd_name: str | None,
    lat: float | None,
    lng: float | None,
    address: str | None,
    number: str | None,
    cep: str | None,
) -> PublicQuoteOut:
    from app.couriers.models import Courier, CourierPricingTable, CourierZona
    from app.teams.models import TeamZona

    nbhd = await resolve_neighborhood(session, area_id=area_id, nbhd_id=nbhd_id, nome=nbhd_name)
    zona_id, zona_name = await _zona_do_destino(
        session,
        area_id=area_id,
        nbhd=nbhd,
        lat=lat,
        lng=lng,
        address=address,
        number=number,
        cep=so_digitos(cep)[:8] or None,
    )

    couriers = list(
        (
            await session.execute(
                select(Courier).where(
                    Courier.area_id == area_id,
                    Courier.is_online.is_(True),
                    Courier.status == "active",
                    Courier.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )

    precos: dict[int, int] = {}
    if zona_id is not None and couriers:
        ids = [c.id for c in couriers]
        inativos = {
            cz.courier_id
            for cz in (
                await session.execute(
                    select(CourierZona).where(
                        CourierZona.zona_id == zona_id,
                        CourierZona.courier_id.in_(ids),
                        CourierZona.ativo.is_(False),
                    )
                )
            ).scalars()
        }
        couriers = [c for c in couriers if c.id not in inativos]
        ids = [c.id for c in couriers]
        proprios = (
            {
                cz.courier_id: cz.preco_cents
                for cz in (
                    await session.execute(
                        select(CourierZona).where(
                            CourierZona.zona_id == zona_id,
                            CourierZona.courier_id.in_(ids),
                            CourierZona.ativo.is_(True),
                        )
                    )
                ).scalars()
            }
            if ids
            else {}
        )
        times = {c.team_id for c in couriers if c.team_id is not None}
        do_time = (
            {
                tz.team_id: tz.preco_minimo_cents
                for tz in (
                    await session.execute(
                        select(TeamZona).where(
                            TeamZona.zona_id == zona_id, TeamZona.team_id.in_(times)
                        )
                    )
                ).scalars()
            }
            if times
            else {}
        )
        couriers = [
            c
            for c in couriers
            if c.id in proprios or (c.team_id is not None and c.team_id in do_time)
        ]
        for c in couriers:
            preco = proprios.get(c.id, do_time.get(c.team_id) if c.team_id is not None else None)
            if preco is not None:
                precos[c.id] = int(preco)
    elif couriers:
        for pr in (
            await session.execute(
                select(CourierPricingTable).where(
                    CourierPricingTable.courier_id.in_([c.id for c in couriers]),
                    CourierPricingTable.area_id == area_id,
                )
            )
        ).scalars():
            if pr.courier_id not in precos and pr.price is not None:
                precos[pr.courier_id] = int(pr.price * 100)

    valores = list(precos.values())
    return PublicQuoteOut(
        dropoff_neighborhood_id=nbhd.id,
        zona_name=zona_name,
        courier_count=len(couriers),
        price_min_cents=min(valores) if valores else None,
        price_max_cents=max(valores) if valores else None,
    )


# ---------------------------------------------------------------------------
# Consulta e cancelamento (entrega da ÁREA da chave; outra área = 404 genérico).
# ---------------------------------------------------------------------------
def cancelavel(state: str) -> bool:
    """Só antes do aceite (RN-019): o que a máquina de estados deixa ir para CANCELADA."""
    return "CANCELADA" in DELIVERY_TRANSITIONS.get(state, set())


async def _delivery_da_area(session: AsyncSession, *, area_id: int, delivery_id: int) -> Delivery:
    delivery = (
        (
            await session.execute(
                select(Delivery).where(Delivery.id == delivery_id, Delivery.area_id == area_id)
            )
        )
        .scalars()
        .first()
    )
    if delivery is None:
        raise NotFoundError("Entrega não encontrada.")
    return delivery


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _ponto(lat: float | None, lng: float | None) -> PublicPoint | None:
    return (
        PublicPoint(lat=float(lat), lng=float(lng)) if lat is not None and lng is not None else None
    )


async def delivery_detail(
    session: AsyncSession, *, area_id: int, delivery_id: int
) -> PublicDeliveryDetail:
    from app.couriers.models import Courier
    from app.ratings.models import CourierRating

    d = await _delivery_da_area(session, area_id=area_id, delivery_id=delivery_id)
    nbhd = (
        await session.get(Neighborhood, d.dropoff_neighborhood_id)
        if d.dropoff_neighborhood_id
        else None
    )
    timeline = [
        PublicTimelineItem(state=to_state, at=_iso(at))
        for to_state, at in (
            await session.execute(
                select(DeliveryStateTransition.to_state, DeliveryStateTransition.created_at)
                .where(DeliveryStateTransition.delivery_id == d.id)
                .order_by(
                    DeliveryStateTransition.created_at.asc(), DeliveryStateTransition.id.asc()
                )
            )
        ).all()
    ]

    courier_out: PublicCourierOut | None = None
    posicao: PublicPoint | None = None
    posicao_em: str | None = None
    if d.courier_id is not None:
        c = await session.get(Courier, d.courier_id)
        if c is not None:
            media = (
                await session.execute(
                    select(func.avg(CourierRating.stars)).where(
                        CourierRating.courier_id == c.id,
                        CourierRating.created_at >= datetime.now(UTC) - timedelta(days=90),
                    )
                )
            ).scalar()
            courier_out = PublicCourierOut(
                name=c.full_name,
                phone_e164=c.phone_e164,
                vehicle_type=c.vehicle_type,
                vehicle_plate=c.vehicle_plate,
                rating=round(float(media), 1) if media is not None else None,
            )
        # Posição só enquanto o entregador está com a entrega (aceite até a entrega)
        # (última ação com GPS ou último ponto do rastro, o mais novo — app manda a cada 1 min)
        if d.state in ("ACEITA", "COLETADA"):
            from app.tracking.trail import ultima_posicao_na_entrega

            loc = await ultima_posicao_na_entrega(session, delivery=d)
            if loc is not None:
                posicao = _ponto(loc.lat, loc.lng)
                posicao_em = _iso(loc.at)

    return PublicDeliveryDetail(
        delivery_id=d.id,
        public_token=d.public_token,
        tracking_url=tracking_url(d.public_token),
        reference_number=d.reference_number,
        state=d.state,
        price_cents=d.price_cents,
        fee_cents=d.fee_cents or 0,
        cancelable=cancelavel(d.state),
        courier=courier_out,
        courier_position=posicao,
        courier_position_at=posicao_em,
        pickup=_ponto(d.pickup_lat, d.pickup_lng),
        dropoff=_ponto(d.dropoff_lat, d.dropoff_lng),
        dropoff_neighborhood=nbhd.name if nbhd else None,
        timeline=timeline,
        created_at=_iso(getattr(d, "created_at", None)),
    )


async def cancel_public_delivery(
    session: AsyncSession, *, area_id: int, delivery_id: int, reason: str | None, ip: str | None
) -> Delivery:
    """Cancela pela API pública: só antes do aceite (a máquina de estados recusa depois — 422)."""
    d = await _delivery_da_area(session, area_id=area_id, delivery_id=delivery_id)
    return await delivery_service.cancel_delivery(
        session,
        area_id=area_id,
        merchant_id=d.merchant_id,
        actor_user_id=None,  # o integrador é o ator
        delivery_id=d.id,
        reason=reason,
        ip=ip,
    )
