"""Delivery service — create, cancel, list, and the state-machine transition.

The transactional core of Phase 7. Every state change goes through `transition()`
(the ONLY writer of `deliveries.state`): it loads the row `FOR UPDATE` (pessimistic
lock — LOW-1 / TH-01), validates against `DELIVERY_TRANSITIONS` (422 if invalid),
updates the state, stamps the per-transition timestamp (aware-UTC — TD-010), and
appends ONE row to the append-only `delivery_state_transitions` history (RN-012).

`create_delivery` (F-03): resolves+validates the dropoff neighborhood against the
area catalog (E1 → 422 fora-de-cobertura), enforces the plan limit server-side
(RN-028 → 402 with upgrade payload), composes the median estimate (RN-030 — E2 →
non-blocking warning, D-06), upserts the recipient (cpf_hash only — D-08), inserts
the delivery in CRIADA and records the initial transition. Cross-tenant access is
closed by (area_id, merchant_id) in the WHERE clause → 404, never 403 (A01 / TH-03).
PII (recipient phone/address/CPF) is NEVER logged (TH-04 / A09).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.core.ratelimit import SlidingWindowLimiter
from app.deliveries.estimate import eligible_online_prices_cents, median_cents
from app.deliveries.models import Delivery, DeliveryStateTransition, Recipient
from app.deliveries.schemas import CreateDeliveryBody, CreateDeliveryResponse
from app.deliveries.state_machine import assert_delivery_transition
from app.merchants.models import MerchantSubscription
from app.neighborhoods.models import Neighborhood
from app.plans.models import SubscriptionPlan

logger = structlog.get_logger("deliveries.service")

# Crockford base32 alphabet for an opaque, non-sequential public token (ULID-like,
# A01 — no new dependency). 26 chars ≈ 130 bits of entropy.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Create rate limit: 30/min per store (TH-07). A busy store peaks at ~1 delivery
# every 2 min; 30/min leaves ample headroom while blocking automated abuse.
delivery_create_limiter = SlidingWindowLimiter(limit=30, window=timedelta(minutes=1))


class PaymentMethodNotAvailableError(AppError):
    """card/pix are not available yet — direct only in Phase 7 (D-02)."""

    status_code = 422
    code = "payment_method_unavailable"

    def __init__(self) -> None:
        super().__init__("Pagamento por cartão ou PIX em breve. Use pagamento direto.")


class DropoffOutOfAreaError(AppError):
    """The dropoff neighborhood is not in the area catalog (F-03 E1 — TH-06)."""

    status_code = 422
    code = "dropoff_out_of_area"

    def __init__(self) -> None:
        super().__init__("Endereço fora da nossa área de cobertura. Confira o bairro.")


class PlanLimitReachedError(AppError):
    """The plan monthly delivery limit was reached (RN-028 / D-07)."""

    status_code = 402
    code = "plan_limit_reached"

    def __init__(self, *, plan_name: str, plan_code: str, limit: int, used: int) -> None:
        self.plan_code = plan_code
        self.limit = limit
        self.used = used
        self.extra: dict[str, object] = {"plan_name": plan_name, "limit": limit, "used": used}
        super().__init__(
            "Você atingiu o limite de entregas do seu plano neste mês. O contador zera no dia 1º."
        )


def hash_cpf(cpf_raw: str) -> str:
    """SHA-256 (hex) of the normalised CPF (digits only). NEVER store the raw CPF."""
    digits = "".join(c for c in cpf_raw if c.isdigit())
    return hashlib.sha256(digits.encode()).hexdigest()


def _new_public_token() -> str:
    """Opaque, non-sequential 26-char token (ULID-like, A01) — no new dependency."""
    return "".join(secrets.choice(_CROCKFORD) for _ in range(26))


def _month_start_utc(now: datetime) -> datetime:
    """First instant of the current month in aware UTC (TD-010)."""
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# State machine transition — the ONLY writer of deliveries.state (A04 / TH-01).
# ---------------------------------------------------------------------------
async def transition(
    session: AsyncSession,
    *,
    delivery: Delivery,
    to_state: str,
    actor_id: int | None,
    reason: str | None = None,
    gps: tuple[float, float] | None = None,
    ip: str | None = None,
    initial: bool = False,
) -> None:
    """Apply a validated state transition under a pessimistic row lock (LOW-1).

    Loads the delivery `FOR UPDATE` so two concurrent transitions serialize; the
    second re-reads the freshly-committed state and raises InvalidTransitionError
    (422) if the move is no longer legal. Writes ONE append-only transition row.

    `initial=True` records the birth of the delivery: the row is already in
    `to_state` (CRIADA) and the history row has `from_state=None`. The machine is
    NOT consulted for the birth (there is no prior state to validate against).
    """
    locked = (
        await session.execute(select(Delivery).where(Delivery.id == delivery.id).with_for_update())
    ).scalar_one()

    if initial:
        from_state = None
    else:
        from_state = locked.state
        assert_delivery_transition(from_state, to_state)  # 422 if invalid

    now = datetime.now(UTC)  # AWARE — TD-010
    locked.state = to_state
    # Stamp the per-transition timestamp.
    _stamp = {
        "ACEITA": "accepted_at",
        "COLETADA": "collected_at",
        "ENTREGUE": "delivered_at",
        "FINALIZADA": "finalized_at",
        "CANCELADA": "cancelled_at",
    }.get(to_state)
    if _stamp is not None:
        setattr(locked, _stamp, now)
    if to_state == "CANCELADA":
        locked.cancel_reason = reason
        locked.cancel_actor_user_id = actor_id

    session.add(
        DeliveryStateTransition(
            area_id=locked.area_id,
            delivery_id=locked.id,
            from_state=from_state,
            to_state=to_state,
            actor_user_id=actor_id,
            reason=reason,
            gps_lat=gps[0] if gps else None,
            gps_lng=gps[1] if gps else None,
            ip=ip,
            created_at=now,
        )
    )
    await session.flush()
    # No PII in the log — only ids/states (A09).
    logger.info(
        "delivery.transition",
        area_id=locked.area_id,
        delivery_id=locked.id,
        from_state=from_state,
        to_state=to_state,
    )

    # Phase 12 (T-07 / D-08): enqueue an outbound webhook for this state change. This
    # is the SINGLE write-point of state, so it is the right hook. NON-BLOCKING by
    # contract — a webhook failure must NEVER derail a delivery transition (try/except;
    # the row is enqueued in the same tx, the arq job delivers it later).
    try:
        from app.webhooks import service as webhook_service

        await webhook_service.enqueue_event(
            session, area_id=locked.area_id, delivery=locked, state=to_state
        )
    except Exception:  # noqa: BLE001 — webhook enqueue is best-effort (D-07)
        logger.warning(
            "delivery.webhook_enqueue_failed",
            area_id=locked.area_id,
            delivery_id=locked.id,
            to_state=to_state,
        )


# ---------------------------------------------------------------------------
# Plan limit (RN-028 / D-07 / LOW-3) — COUNT server-side, CANCELADA excluded.
# ---------------------------------------------------------------------------
async def deliveries_this_month(session: AsyncSession, *, merchant_id: int, area_id: int) -> int:
    """COUNT of the merchant's non-cancelled deliveries this month (RN-028 / LOW-3).

    CANCELADA is EXCLUDED (RN-004: a pre-acceptance cancel costs nothing and must
    not let a store burn a slot by create+cancel). Uses the
    (area_id, merchant_id, created_at) index — no table scan.
    """
    start = _month_start_utc(datetime.now(UTC))
    stmt = select(func.count(Delivery.id)).where(
        Delivery.area_id == area_id,
        Delivery.merchant_id == merchant_id,
        Delivery.created_at >= start,
        Delivery.state != "CANCELADA",
    )
    return int((await session.execute(stmt)).scalar_one())


async def _active_plan(
    session: AsyncSession, *, merchant_id: int, area_id: int
) -> SubscriptionPlan:
    """Load the merchant's active subscription plan (or 404 if none)."""
    stmt = (
        select(SubscriptionPlan)
        .join(MerchantSubscription, MerchantSubscription.plan_id == SubscriptionPlan.id)
        .where(
            MerchantSubscription.merchant_id == merchant_id,
            MerchantSubscription.area_id == area_id,
            MerchantSubscription.status == "active",
        )
    )
    plan = (await session.execute(stmt)).scalars().first()
    if plan is None:
        raise NotFoundError("Assinatura ativa não encontrada.")
    return plan


async def _assert_within_plan_limit(
    session: AsyncSession, *, merchant_id: int, area_id: int
) -> None:
    """Enforce the plan monthly limit server-side (RN-028). Unlimited tiers pass."""
    plan = await _active_plan(session, merchant_id=merchant_id, area_id=area_id)
    if plan.is_unlimited:
        return
    used = await deliveries_this_month(session, merchant_id=merchant_id, area_id=area_id)
    if used >= plan.deliveries_per_month:
        raise PlanLimitReachedError(plan_name=plan.name, plan_code=plan.code, limit=plan.deliveries_per_month, used=used)


# ---------------------------------------------------------------------------
# Recipient upsert (D-08 / LGPD) — cpf_hash only, minimisation.
# ---------------------------------------------------------------------------
async def upsert_recipient(
    session: AsyncSession, *, area_id: int, body: CreateDeliveryBody
) -> Recipient:
    """Create (or reuse) the recipient; store only cpf_hash, never the raw CPF."""
    cpf_hash = hash_cpf(body.recipient_cpf) if body.recipient_cpf else None
    recipient = Recipient(
        area_id=area_id,
        name=body.recipient_name,
        phone_e164=body.recipient_phone_e164,
        email=body.recipient_email,
        cpf_hash=cpf_hash,
        deliveries_count=0,
        refusals_count=0,
    )
    session.add(recipient)
    await session.flush()
    return recipient


# ---------------------------------------------------------------------------
# Create (F-03) — the happy path + E1/E2/E4 exceptions.
# ---------------------------------------------------------------------------
async def _resolve_dropoff_neighborhood(
    session: AsyncSession, *, area_id: int, nbhd_id: int
) -> Neighborhood:
    """Resolve the dropoff neighborhood in THIS area's catalog (E1 → 422)."""
    stmt = select(Neighborhood).where(
        Neighborhood.id == nbhd_id,
        Neighborhood.area_id == area_id,
        Neighborhood.archived_at.is_(None),
    )
    nbhd = (await session.execute(stmt)).scalars().first()
    if nbhd is None:
        raise DropoffOutOfAreaError()
    return nbhd


async def create_delivery(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    actor_user_id: int | None,
    body: CreateDeliveryBody,
    ip: str | None,
    pickup_nbhd_id: int | None = None,
    payment_service: object | None = None,
    card_blob: str | None = None,
    customer_document: str | None = None,
    customer_email: str | None = None,
    pix_payment_port: object | None = None,
) -> CreateDeliveryResponse:
    """Create a delivery in CRIADA (F-03). `direct` is free; card/pix charges first.

    For `card`/`pix` (Phase 10): the platform charges corrida+taxa with a split BEFORE the
    delivery is inserted. A refusal/outage raises `PaymentGatewayError` and the delivery is
    NOT created (F-03 E3 — the caller never reaches the insert). `direct` is untouched, so a
    gateway outage never blocks it (circuit breaker — REQ-034). The split/charge wiring is
    delegated to the injected `payment_service` (a `PaymentService`); when absent (default),
    only `direct` is accepted.
    """
    method = body.payment_method.value
    # Phase 7 left card/pix "em breve"; Phase 10 activates them only when a payment service
    # is wired. Without it (legacy callers), card/pix is still unavailable.
    if method != "direct" and payment_service is None:
        raise PaymentMethodNotAvailableError()

    # Subscription guard (SAAS-BILLING §9): blocked/cancelado stores cannot create.
    from app.payments.subscriptions import assert_subscription_active

    await assert_subscription_active(session, merchant_id=merchant_id, area_id=area_id)

    # Overdue-invoice guard (F-03 E5 / Phase 15): a platform-fee invoice overdue more
    # than the parametrised threshold (>7d) blocks creation server-side (TH-08). Same
    # point as the subscription guard (D-02).
    from app.invoices.service import InvoiceOverdueError, is_blocked_by_overdue_invoice

    if await is_blocked_by_overdue_invoice(session, area_id=area_id, merchant_id=merchant_id):
        raise InvoiceOverdueError()

    # E1: the dropoff neighborhood must be in the area catalog.
    await _resolve_dropoff_neighborhood(
        session, area_id=area_id, nbhd_id=body.dropoff_neighborhood_id
    )

    # E4: plan limit (RN-028) — server-side, before any write.
    await _assert_within_plan_limit(session, merchant_id=merchant_id, area_id=area_id)

    # Estimate (RN-030): median of eligible online couriers for the trip.
    # The pickup neighborhood id is optional in Phase 7 (the UI may not resolve a
    # polygon yet); when absent, eligibility uses the dropoff id for both points so
    # a single-neighborhood courier still contributes a price.
    pickup_id = pickup_nbhd_id if pickup_nbhd_id is not None else body.dropoff_neighborhood_id
    prices = await eligible_online_prices_cents(
        session,
        area_id=area_id,
        pickup_nbhd_id=pickup_id,
        dropoff_nbhd_id=body.dropoff_neighborhood_id,
        distance_m=body.distance_m,
    )
    no_couriers_warning = len(prices) == 0

    recipient = await upsert_recipient(session, area_id=area_id, body=body)

    # Scheduled delivery: use AGENDADA as initial state; Inngest will transition
    # to CRIADA at the scheduled time. Platform PIX: AGUARDANDO_PAGAMENTO until paid.
    # Immediate delivery without PIX stays CRIADA (current path).
    scheduled_at = getattr(body, "scheduled_at", None)
    platform_pix = getattr(body, "platform_pix", False) and pix_payment_port is not None
    if scheduled_at is not None:
        initial_state = "AGENDADA"
    elif platform_pix:
        initial_state = "AGUARDANDO_PAGAMENTO"
    else:
        initial_state = "CRIADA"

    delivery = Delivery(
        area_id=area_id,
        merchant_id=merchant_id,
        courier_id=None,
        recipient_id=recipient.id,
        state=initial_state,
        dispatch_mode="direct",
        payment_method=method,
        proof_method=body.proof_method.value,
        pickup_address=body.pickup_address,
        pickup_neighborhood=body.pickup_neighborhood,
        pickup_lat=getattr(body, "pickup_lat", None),
        pickup_lng=getattr(body, "pickup_lng", None),
        dropoff_address=body.dropoff_address,
        dropoff_number=body.dropoff_number,
        dropoff_complement=body.dropoff_complement,
        dropoff_reference=body.dropoff_reference,
        dropoff_neighborhood_id=body.dropoff_neighborhood_id,
        dropoff_lat=getattr(body, "dropoff_lat", None),
        dropoff_lng=getattr(body, "dropoff_lng", None),
        distance_m=body.distance_m,
        fee_cents=0,
        items_description=body.items_description,
        items_quantity=body.items_quantity,
        declared_value_cents=body.declared_value_cents,
        weight_g=body.weight_g,
        length_cm=body.length_cm,
        width_cm=body.width_cm,
        height_cm=body.height_cm,
        reference_number=body.reference_number,
        notes=body.notes,
        receipt_method=body.receipt_method,
        team_ids=body.team_ids,
        public_token=_new_public_token(),
        origin="manual",
        scheduled_at=scheduled_at,
    )
    session.add(delivery)
    await session.flush()

    # Find zone from dropoff coordinates (point-in-polygon).
    # Prefer explicit lat/lng from body; fall back to geocoding the address.
    dlat = getattr(body, "dropoff_lat", None)
    dlng = getattr(body, "dropoff_lng", None)
    if dlat is None or dlng is None:
        from app.areas.models import Area
        from app.integrations.factory import get_geocoding_adapter
        from app.neighborhoods.models import Neighborhood as _Nbhd
        area = await session.get(Area, area_id)
        nbhd = await session.get(_Nbhd, body.dropoff_neighborhood_id)
        address_parts = [
            body.dropoff_address,
            getattr(body, "dropoff_number", None),
            nbhd.name if nbhd else None,
            getattr(body, "cep", None),
            area.name if area else None,
        ]
        address_str = ", ".join(p for p in address_parts if p)
        geo = await get_geocoding_adapter().geocode(address_str)
        if geo is not None:
            dlat, dlng = geo.lat, geo.lng
            delivery.dropoff_lat = dlat
            delivery.dropoff_lng = dlng
    if dlat is not None and dlng is not None:
        from app.areas.zona_finder import find_zona_id
        delivery.zona_id = await find_zona_id(session, area_id=area_id, lat=dlat, lng=dlng)

    # Platform PIX delivery (Phase 12): generate PIX QR directed to itcast subconta.
    # The delivery stays in AGUARDANDO_PAGAMENTO until the webhook confirms payment.
    pix_qr_code: str | None = None
    pix_qr_code_base64: str | None = None
    if platform_pix:
        from app.core.config import get_settings
        from app.merchants.models import Merchant
        from app.payments.port import Customer

        pix_amount = getattr(body, "pix_amount_cents", None) or 0
        merchant = await session.get(Merchant, merchant_id)
        pix_customer = Customer(
            name=merchant.trade_name if merchant else "Loja",
            document=merchant.document if merchant else "00000000000",
            email=merchant.email if merchant else "",
            zip_code=merchant.address_zip if merchant else None,
            street=merchant.address if merchant else None,
            street_number=merchant.address_number if merchant else "S/N",
            neighborhood=merchant.address_neighborhood if merchant else None,
            state=merchant.address_state if merchant else None,
        )
        now_ts = int(datetime.now(UTC).timestamp())
        pix_ref = f"delivery-{delivery.id}-pix-{now_ts}"
        pix_result = await pix_payment_port.create_pix_authorization(  # type: ignore[union-attr]
            amount_cents=pix_amount,
            customer=pix_customer,
            reference=pix_ref,
            recorrente=False,
        )
        delivery.pix_transaction_id = pix_result.transaction_id or None
        delivery.pix_qr_code = pix_result.qr_code or None
        delivery.pix_qr_code_base64 = pix_result.qr_code_base64 or None
        pix_qr_code = delivery.pix_qr_code
        pix_qr_code_base64 = delivery.pix_qr_code_base64
        await session.flush()

        from app.payments import repo as payments_repo

        await payments_repo.record_charge(
            session,
            area_id=area_id,
            idempotency_key=pix_ref,
            transaction_id=pix_result.transaction_id,
            amount_cents=pix_amount,
            method="pix",
            kind="delivery",
            status="open",
            delivery_id=delivery.id,
        )

    # Card/PIX (Phase 10): charge corrida+taxa with a split BEFORE finalising. A refusal/
    # outage raises PaymentGatewayError → the caller's transaction rolls back and the
    # delivery is NOT created (F-03 E3). `direct` skips this entirely (circuit breaker).
    if method != "direct" and payment_service is not None:
        from app.payments.service import PaymentService

        assert isinstance(payment_service, PaymentService)
        corrida_cents = estimate or 0
        plan = await _active_plan(session, merchant_id=merchant_id, area_id=area_id)
        taxa_cents = plan.fee_cents
        await payment_service.charge_delivery(
            area_id=area_id,
            delivery_id=delivery.id,
            corrida_cents=corrida_cents,
            taxa_cents=taxa_cents,
            courier_recipient="",  # resolved on acceptance (Phase 8); split recipient set later
            method=method,
            customer_name=recipient.name,
            customer_document=customer_document or "",
            customer_email=customer_email or (recipient.email or ""),
        )
        delivery.fee_cents = taxa_cents
    elif method == "direct":
        # Phase 15 (RN-025): direct deliveries carry NO online charge, but the platform
        # fee is RECORDED here so the monthly invoice (`invoices/`) can aggregate it (the
        # effective charge is the Phase 15 invoice). Derived from the active plan — never
        # user input (TH-03).
        plan = await _active_plan(session, merchant_id=merchant_id, area_id=area_id)
        delivery.fee_cents = plan.fee_cents

    # Initial transition None → CRIADA or AGENDADA (the single writer of state).
    await transition(
        session,
        delivery=delivery,
        to_state=initial_state,
        actor_id=actor_user_id,
        reason="scheduled" if initial_state == "AGENDADA" else None,
        ip=ip,
        initial=True,
    )

    # Scheduled: register with Inngest and store the event ID.
    inngest_event_id: str | None = None
    if initial_state == "AGENDADA" and scheduled_at is not None:
        from app.integrations.inngest import get_inngest_client

        inngest_event_id = await get_inngest_client().schedule(delivery.id, scheduled_at)
        if inngest_event_id is not None:
            delivery.inngest_event_id = inngest_event_id
            await session.flush()

    logger.info(
        "delivery.created",
        area_id=area_id,
        merchant_id=merchant_id,
        delivery_id=delivery.id,
        eligible_couriers=len(prices),
        scheduled=initial_state == "AGENDADA",
    )
    scheduled_at_iso = scheduled_at.isoformat() if scheduled_at is not None else None
    return CreateDeliveryResponse(
        delivery_id=delivery.id,
        public_token=delivery.public_token,
        state=delivery.state,
        price_cents=delivery.price_cents,
        fee_cents=delivery.fee_cents,
        no_couriers_warning=no_couriers_warning,
        scheduled_at=scheduled_at_iso,
        pix_qr_code=pix_qr_code,
        pix_qr_code_base64=pix_qr_code_base64,
    )


# ---------------------------------------------------------------------------
# Read / cancel — IDOR closed by (area_id, merchant_id) → 404 (A01 / TH-03).
# ---------------------------------------------------------------------------
async def get_delivery(
    session: AsyncSession, *, area_id: int, merchant_id: int, delivery_id: int
) -> Delivery:
    """Load a delivery owned by this store in this area, or 404 (no existence leak)."""
    stmt = select(Delivery).where(
        Delivery.id == delivery_id,
        Delivery.area_id == area_id,
        Delivery.merchant_id == merchant_id,
    )
    delivery = (await session.execute(stmt)).scalars().first()
    if delivery is None:
        raise NotFoundError("Entrega não encontrada.")
    return delivery


# ---------------------------------------------------------------------------
# RN-004 cancellation cost + RN-013 dropoff reveal (Phase 9 — F-06).
# ---------------------------------------------------------------------------
# The full dropoff address is revealed ONLY after pickup (RN-013) — by state.
_DROPOFF_REVEALED_STATES = frozenset({"COLETADA", "ENTREGUE", "FINALIZADA"})


def dropoff_revealed(state: str) -> bool:
    """True if the full dropoff address may be shown for this state (RN-013)."""
    return state in _DROPOFF_REVEALED_STATES


def cancellation_cost_cents(delivery: Delivery, *, return_pct: int) -> int:
    """RN-004 cost (cents) for cancelling NOW, by the delivery's current state.

    - CRIADA (pre-acceptance): 0 (the store may free-cancel before a courier accepts).
    - SEM_RESPOSTA (cascade exhausted, no courier accepted yet): 0, same as CRIADA.
    - ACEITA (accepted, not collected): 50% of the estimate.
    - COLETADA (collected): 100% of the estimate + the area's return policy %.

    The price base is `price_cents` (or 0 if not yet accepted). This is only
    RECORDED on the delivery; the effective charge is the Phase 11 invoice.
    """
    base = delivery.price_cents or 0
    state = delivery.state
    if state in ("AGENDADA", "AGUARDANDO_PAGAMENTO", "CRIADA", "SEM_RESPOSTA"):
        return 0
    if state == "ACEITA":
        return base // 2
    if state == "COLETADA":
        return base + (base * max(return_pct, 0)) // 100
    # Terminal states are not cancellable (the transition will 422); cost 0.
    return 0


async def cancel_delivery(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    actor_user_id: int | None,
    delivery_id: int,
    reason: str | None,
    ip: str | None,
) -> Delivery:
    """Cancel a delivery the store owns; RECORD the RN-004 cost by state (Phase 9)."""
    delivery = await get_delivery(
        session, area_id=area_id, merchant_id=merchant_id, delivery_id=delivery_id
    )
    cost = cancellation_cost_cents(delivery, return_pct=0)

    await transition(
        session,
        delivery=delivery,
        to_state="CANCELADA",
        actor_id=actor_user_id,
        reason=reason,
        ip=ip,
    )
    delivery.cancel_cost_cents = cost  # recorded (charge is Phase 11)
    await session.flush()
    return delivery


async def list_deliveries(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    state: str | None = None,
    payment_method: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> DeliveryPage:
    """Paginated store delivery list (single query + COUNT — no N+1, TH-03)."""
    base = (
        select(Delivery, Recipient)
        .outerjoin(Recipient, Recipient.id == Delivery.recipient_id)
        .where(Delivery.area_id == area_id, Delivery.merchant_id == merchant_id)
    )
    count_stmt = select(func.count(Delivery.id)).where(
        Delivery.area_id == area_id, Delivery.merchant_id == merchant_id
    )
    if state is not None:
        base = base.where(Delivery.state == state)
        count_stmt = count_stmt.where(Delivery.state == state)
    if payment_method is not None:
        base = base.where(Delivery.payment_method == payment_method)
        count_stmt = count_stmt.where(Delivery.payment_method == payment_method)

    base = base.order_by(Delivery.created_at.desc()).limit(limit).offset(offset)
    rows = list((await session.execute(base)).all())
    total = int((await session.execute(count_stmt)).scalar_one())
    items = [(delivery, recipient) for delivery, recipient in rows]
    return DeliveryPage(items=items, total=total, limit=limit, offset=offset)


class DeliveryPage:
    """Lightweight page container (router maps it to DeliveryListOut)."""

    __slots__ = ("items", "total", "limit", "offset")

    def __init__(
        self,
        *,
        items: list[tuple[Delivery, Recipient | None]],
        total: int,
        limit: int,
        offset: int,
    ) -> None:
        self.items = items
        self.total = total
        self.limit = limit
        self.offset = offset


# ---------------------------------------------------------------------------
# Courier-facing reads (F1.0 / MR-1): the ASSIGNED courier reads their own
# delivery. Scoped by courier_id (the router proves the courier belongs to the
# authenticated user — IDOR → 404). PII reveal-by-state is done in the router's
# serializer (RN-013): full dropoff + recipient only AFTER pickup.
# ---------------------------------------------------------------------------
_COURIER_ACTIVE_STATES = frozenset({"ACEITA", "COLETADA"})


async def get_courier_delivery(
    session: AsyncSession, *, courier_id: int, delivery_id: int
) -> tuple[Delivery, Recipient | None]:
    """Read one delivery assigned to this courier (404 if not theirs — TH-03)."""
    stmt = select(Delivery).where(Delivery.id == delivery_id, Delivery.courier_id == courier_id)
    delivery = (await session.execute(stmt)).scalar_one_or_none()
    if delivery is None:
        raise NotFoundError("Entrega não encontrada.")
    recipient = (
        await session.get(Recipient, delivery.recipient_id)
        if delivery.recipient_id is not None
        else None
    )
    return delivery, recipient


async def get_courier_active_delivery(
    session: AsyncSession, *, courier_id: int
) -> tuple[Delivery, Recipient | None] | None:
    """The courier's single in-progress delivery (ACEITA/COLETADA), if any."""
    stmt = (
        select(Delivery)
        .where(Delivery.courier_id == courier_id, Delivery.state.in_(_COURIER_ACTIVE_STATES))
        .order_by(Delivery.accepted_at.desc())
        .limit(1)
    )
    delivery = (await session.execute(stmt)).scalar_one_or_none()
    if delivery is None:
        return None
    recipient = (
        await session.get(Recipient, delivery.recipient_id)
        if delivery.recipient_id is not None
        else None
    )
    return delivery, recipient


async def get_courier_active_deliveries(
    session: AsyncSession, *, courier_id: int
) -> list[tuple[Delivery, Recipient | None]]:
    """All of the courier's in-progress deliveries (ACEITA/COLETADA), newest first."""
    stmt = (
        select(Delivery)
        .where(Delivery.courier_id == courier_id, Delivery.state.in_(_COURIER_ACTIVE_STATES))
        .order_by(Delivery.accepted_at.desc())
    )
    deliveries = (await session.execute(stmt)).scalars().all()
    results: list[tuple[Delivery, Recipient | None]] = []
    for delivery in deliveries:
        recipient = (
            await session.get(Recipient, delivery.recipient_id)
            if delivery.recipient_id is not None
            else None
        )
        results.append((delivery, recipient))
    return results


async def release_scheduled_delivery(
    session: AsyncSession,
    *,
    delivery_id: int,
) -> bool:
    """Transition AGENDADA → CRIADA and kick off the dispatch cascade.

    Called by the Inngest webhook at the scheduled time. Returns True if the
    delivery was released, False if it was already in a different state (e.g.
    the store cancelled it before Inngest fired — idempotent).
    """
    stmt = select(Delivery).where(Delivery.id == delivery_id)
    delivery = (await session.execute(stmt)).scalar_one_or_none()
    if delivery is None:
        logger.warning("release_scheduled.not_found", delivery_id=delivery_id)
        return False
    if delivery.state != "AGENDADA":
        logger.info(
            "release_scheduled.skip",
            delivery_id=delivery_id,
            state=delivery.state,
        )
        return False  # already cancelled / released — idempotent

    await transition(
        session,
        delivery=delivery,
        to_state="CRIADA",
        actor_id=None,
        reason="inngest_scheduled_release",
    )
    await session.commit()
    logger.info("release_scheduled.released", delivery_id=delivery_id)
    return True


async def move_to_unanswered_pool(
    session: AsyncSession,
    *,
    delivery_id: int,
) -> bool:
    """Transition CRIADA → SEM_RESPOSTA: every eligible courier exhausted their
    chances (declined OR hit the timeout cap — `app/workers/dispatch.py`). The
    delivery leaves the cascade entirely and becomes browsable in the "Entregas
    sem resposta" pool, where any courier may self-assign it. Idempotent — a
    concurrent caller finding the delivery already moved on is a no-op.
    """
    stmt = select(Delivery).where(Delivery.id == delivery_id)
    delivery = (await session.execute(stmt)).scalar_one_or_none()
    if delivery is None:
        logger.warning("move_to_pool.not_found", delivery_id=delivery_id)
        return False
    if delivery.state != "CRIADA":
        logger.info("move_to_pool.skip", delivery_id=delivery_id, state=delivery.state)
        return False  # already moved on (accepted/cancelled) — idempotent

    await transition(
        session,
        delivery=delivery,
        to_state="SEM_RESPOSTA",
        actor_id=None,
        reason="dispatch_cascade_exhausted",
    )
    logger.info("move_to_pool.moved", delivery_id=delivery_id)
    return True


async def list_courier_deliveries(
    session: AsyncSession, *, courier_id: int, limit: int = 20, offset: int = 0
) -> DeliveryPage:
    """Paginated history of the courier's deliveries (single query + COUNT)."""
    base = (
        select(Delivery, Recipient)
        .outerjoin(Recipient, Recipient.id == Delivery.recipient_id)
        .where(Delivery.courier_id == courier_id)
        .order_by(Delivery.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    count_stmt = select(func.count(Delivery.id)).where(Delivery.courier_id == courier_id)
    rows = list((await session.execute(base)).all())
    total = int((await session.execute(count_stmt)).scalar_one())
    items = [(d, r) for d, r in rows]
    return DeliveryPage(items=items, total=total, limit=limit, offset=offset)
