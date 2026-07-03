"""Dispatch service — offer view (RN-013), accept (lock), decline, cancel.

`build_offer_view` constructs the courier-facing `OfferOut` from the ALLOWED
columns only (RN-013 — never the full dropoff address; Pitfall 2). `accept_offer`
is the critical piece (D-05): redis `Lock` + `SELECT ... FOR UPDATE` (reuses Phase
7 `transition()`) + the idempotent CRIADA→ACEITA machine decide the single winner;
the second concurrent accept gets `OfferAlreadyTakenError` (409) with ZERO penalty
(F-05 E3 / Pitfall 1). The lock is released via `Lock.release()` (token-checked,
never a manual DEL — Pitfall 5). All timestamps are aware UTC (TD-010).
"""

from __future__ import annotations

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.models import Courier, CourierPricingTable, CourierZona
from app.db.mixins import ensure_aware_utc
from app.deliveries.estimate import effective_price_cents
from app.deliveries.models import Delivery
from app.deliveries.service import transition
from app.deliveries.state_machine import InvalidTransitionError
from app.dispatch import offer_state
from app.dispatch.exceptions import NotOfferTargetError, OfferAlreadyTakenError
from app.dispatch.schemas import OfferOut, PoolItemOut
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from app.teams.models import TeamZona

logger = structlog.get_logger("dispatch.service")

LOCK_TIMEOUT_S = 10
LOCK_BLOCKING_S = 2


async def _zone_price_cents(
    session: AsyncSession,
    *,
    courier_id: int,
    zona_id: int | None,
) -> int | None:
    """Courier price for a zone: courier override → team min → None (use fallback)."""
    if zona_id is None:
        return None
    cz = (await session.execute(
        select(CourierZona).where(
            CourierZona.courier_id == courier_id,
            CourierZona.zona_id == zona_id,
        )
    )).scalar_one_or_none()
    if cz is not None:
        return cz.preco_cents

    courier = await session.get(Courier, courier_id)
    if courier is not None and courier.team_id is not None:
        tz = (await session.execute(
            select(TeamZona).where(
                TeamZona.team_id == courier.team_id,
                TeamZona.zona_id == zona_id,
            )
        )).scalar_one_or_none()
        if tz is not None:
            return tz.preco_minimo_cents
    return None


async def build_offer_view(
    session: AsyncSession,
    r: aioredis.Redis,
    *,
    delivery: Delivery,
) -> OfferOut:
    """Build the courier offer (RN-013: neighborhood + distance ONLY).

    Constructed field-by-field from the allowed columns — NEVER from_attributes
    over the whole Delivery (the full dropoff address must not even be reachable
    here, Pitfall 2). Reads the Redis offer for the authoritative timer (ADR-104).
    """
    merchant = await session.get(Merchant, delivery.merchant_id)
    nbhd = await session.get(Neighborhood, delivery.dropoff_neighborhood_id)
    offer = await offer_state.current_offer(r, delivery.id)
    timeout_s = int(offer["timeout_s"]) if offer and "timeout_s" in offer else 0
    remaining = await offer_state.offer_ttl_remaining_s(r, delivery.id)

    # Resolve the courier's own price for this trip (zone → pricing table).
    courier_price = delivery.price_cents
    if offer and "courier_id" in offer:
        courier_id = int(offer["courier_id"])
        zone_price = await _zone_price_cents(session, courier_id=courier_id, zona_id=delivery.zona_id)
        if zone_price is not None:
            courier_price = zone_price
        else:
            pricing_rows = list(
                (await session.execute(
                    select(CourierPricingTable).where(
                        CourierPricingTable.courier_id == courier_id,
                        CourierPricingTable.area_id == delivery.area_id,
                    )
                )).scalars().all()
            )
            price = effective_price_cents(
                pricing_rows,
                dropoff_nbhd_id=delivery.dropoff_neighborhood_id,
                distance_m=delivery.distance_m,
            )
            if price is not None:
                courier_price = price

    return OfferOut(
        delivery_id=delivery.id,
        loja_nome=merchant.trade_name if merchant else "",
        pickup_address=delivery.pickup_address,
        pickup_neighborhood=delivery.pickup_neighborhood,
        dropoff_address=delivery.dropoff_address,
        dropoff_number=delivery.dropoff_number,
        dropoff_neighborhood=nbhd.name if nbhd else "",
        distance_m=delivery.distance_m,
        value_cents=courier_price,
        payment_method=delivery.payment_method,
        receipt_method=delivery.receipt_method,
        eta_s=None,
        eta_degraded=False,
        ttl_total_s=timeout_s,
        ttl_remaining_s=remaining if remaining is not None else 0,
    )


async def accept_offer(
    session: AsyncSession,
    r: aioredis.Redis,
    *,
    area_id: int,
    delivery_id: int,
    courier_id: int,
    actor_user_id: int | None,
    ip: str | None,
) -> Delivery:
    """Accept an offer — single winner via Lock + FOR UPDATE + state machine (D-05).

    The 2nd concurrent accept falls into ONE of these and gets 409 WITHOUT penalty
    (F-05 E3 / Pitfall 1): lock not acquired in time, OR state != CRIADA after the
    FOR UPDATE, OR the CRIADA→ACEITA machine rejects (InvalidTransitionError).
    """
    # A01 (TH-4): only the courier targeted by the CURRENT offer may accept. 404,
    # never 403 — do not leak that an offer exists for someone else.
    offer = await offer_state.current_offer(r, delivery_id)
    if offer is None or offer.get("courier_id") != courier_id:
        raise NotOfferTargetError()

    lock = r.lock(
        f"accept:{delivery_id}",
        timeout=LOCK_TIMEOUT_S,
        blocking_timeout=LOCK_BLOCKING_S,
    )
    acquired = await lock.acquire()
    if not acquired:
        # Someone else is accepting right now — non-event, no penalty.
        raise OfferAlreadyTakenError()
    try:
        # FOR UPDATE serializes at the DB; the 2nd re-reads the committed state.
        locked = (
            await session.execute(
                select(Delivery)
                .where(Delivery.id == delivery_id, Delivery.area_id == area_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if locked is None:
            raise NotOfferTargetError()
        if locked.state != "CRIADA":
            # Already accepted/cancelled — the race is lost. No penalty (F-05 E3).
            raise OfferAlreadyTakenError()
        try:
            locked.courier_id = courier_id
            # Zone price takes priority; fall back to old pricing table.
            zone_price = await _zone_price_cents(session, courier_id=courier_id, zona_id=locked.zona_id)
            if zone_price is not None:
                locked.price_cents = zone_price
            else:
                pricing_rows = list(
                    (await session.execute(
                        select(CourierPricingTable).where(
                            CourierPricingTable.courier_id == courier_id,
                            CourierPricingTable.area_id == area_id,
                        )
                    )).scalars().all()
                )
                locked.price_cents = effective_price_cents(
                    pricing_rows,
                    dropoff_nbhd_id=locked.dropoff_neighborhood_id,
                    distance_m=locked.distance_m,
                )
            await transition(
                session,
                delivery=locked,
                to_state="ACEITA",
                actor_id=actor_user_id,
                ip=ip,
            )
        except InvalidTransitionError as exc:
            raise OfferAlreadyTakenError() from exc

        # Close the offer + cancel the rest of the cascade (queue + reverse index).
        await offer_state.close_offer(r, delivery_id)
        await offer_state.clear_candidates(r, delivery_id)

        # KPI NORTE (observability) — tempo criação→aceite, no PII. Coerce both to
        # aware UTC at the read boundary (TD-010): SQLite/MySQL read back naive.
        elapsed_ms: int | None = None
        if locked.created_at is not None and locked.accepted_at is not None:
            created = ensure_aware_utc(locked.created_at)
            accepted = ensure_aware_utc(locked.accepted_at)
            elapsed_ms = int((accepted - created).total_seconds() * 1000)
        logger.info(
            "dispatch.offer.accepted",
            area_id=area_id,
            delivery_id=delivery_id,
            courier_id=courier_id,
            elapsed_ms=elapsed_ms,
        )
        return locked
    finally:
        # Token-checked release (Lua) — never a manual DEL (Pitfall 5).
        try:
            await lock.release()
        except Exception:  # noqa: BLE001 — lock may have expired; safe to ignore
            pass


async def cancel_pending_offers(r: aioredis.Redis, *, delivery_id: int) -> None:
    """Cancel any pending offer + candidate queue for a delivery (E4 / accept).

    Used when the store cancels a CRIADA delivery during the cascade (E4 — zero
    cost, RN-004) and after an accept. Couriers holding the offer fall into
    "expired" on their next poll (the offer key is gone).
    """
    await offer_state.close_offer(r, delivery_id)
    await offer_state.clear_candidates(r, delivery_id)
    logger.info("dispatch.offer.cancelled", delivery_id=delivery_id)


# ---------------------------------------------------------------------------
# Unanswered pool — deliveries that exhausted the cascade (every eligible
# courier declined or hit the timeout cap, `app/workers/dispatch.py`). Any
# courier who could have been offered it may browse + self-assign it.
# ---------------------------------------------------------------------------
async def list_unanswered_pool(
    session: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
) -> list[PoolItemOut]:
    """SEM_RESPOSTA deliveries this courier could self-assign.

    Filtered by the SAME eligibility the cascade applies (RN-003 coverage at both
    points + team match, `cascade.build_candidates`) — a courier never sees a
    delivery it could not have legitimately served. Oldest first (most overdue).
    """
    courier = await session.get(Courier, courier_id)
    if courier is None or courier.area_id != area_id:
        return []

    deliveries = list(
        (
            await session.execute(
                select(Delivery)
                .where(Delivery.area_id == area_id, Delivery.state == "SEM_RESPOSTA")
                .order_by(Delivery.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    # Pre-load courier zone rows once — used for both eligibility and pricing.
    cz_rows = list(
        (await session.execute(
            select(CourierZona).where(CourierZona.courier_id == courier_id)
        )).scalars()
    )
    zona_inactive_ids: set[int] = {cz.zona_id for cz in cz_rows if not cz.ativo}
    cz_map: dict[int, int] = {cz.zona_id: cz.preco_cents for cz in cz_rows if cz.ativo}

    eligible = [
        d
        for d in deliveries
        if (not d.team_ids or courier.team_id in d.team_ids)
        and (d.zona_id is None or d.zona_id not in zona_inactive_ids)
    ]
    if not eligible:
        return []

    merchant_ids = {d.merchant_id for d in eligible}
    nbhd_ids = {d.dropoff_neighborhood_id for d in eligible}
    merchants = {
        m.id: m
        for m in (
            await session.execute(select(Merchant).where(Merchant.id.in_(merchant_ids)))
        ).scalars()
    }
    neighborhoods = {
        n.id: n
        for n in (
            await session.execute(select(Neighborhood).where(Neighborhood.id.in_(nbhd_ids)))
        ).scalars()
    }
    pricing_rows = list(
        (await session.execute(
            select(CourierPricingTable).where(CourierPricingTable.courier_id == courier_id)
        )).scalars()
    )
    tz_map: dict[int, int] = {}
    if courier is not None and courier.team_id is not None:
        tz_map = {
            tz.zona_id: tz.preco_minimo_cents
            for tz in (await session.execute(
                select(TeamZona).where(TeamZona.team_id == courier.team_id)
            )).scalars()
        }

    def _price(d: Delivery) -> int | None:
        if d.zona_id is not None:
            if d.zona_id in cz_map:
                return cz_map[d.zona_id]
            if d.zona_id in tz_map:
                return tz_map[d.zona_id]
        return effective_price_cents(
            pricing_rows,
            dropoff_nbhd_id=d.dropoff_neighborhood_id,
            distance_m=d.distance_m,
        )

    return [
        PoolItemOut(
            delivery_id=d.id,
            loja_nome=merchants[d.merchant_id].trade_name if d.merchant_id in merchants else "",
            pickup_address=d.pickup_address,
            pickup_neighborhood=d.pickup_neighborhood,
            dropoff_address=d.dropoff_address or "",
            dropoff_number=d.dropoff_number,
            dropoff_neighborhood=(
                neighborhoods[d.dropoff_neighborhood_id].name
                if d.dropoff_neighborhood_id in neighborhoods
                else ""
            ),
            distance_m=d.distance_m,
            value_cents=_price(d),
            payment_method=d.payment_method,
            receipt_method=d.receipt_method,
            created_at=ensure_aware_utc(d.created_at).isoformat() if d.created_at else "",
        )
        for d in eligible
    ]


async def self_assign_pool_delivery(
    session: AsyncSession,
    r: aioredis.Redis,
    *,
    area_id: int,
    delivery_id: int,
    courier_id: int,
    actor_user_id: int | None,
    ip: str | None,
) -> Delivery:
    """A courier claims a SEM_RESPOSTA delivery from the pool (D-05 pattern).

    Mirrors `accept_offer`'s race protection exactly (Lock + FOR UPDATE + state
    machine), since the pool has the same "single winner" problem as an offer —
    several couriers may tap the same card at once. Loser gets 409, zero penalty
    (no offer was ever targeted at them, so F-05 E3 applies the same way).
    """
    lock = r.lock(
        f"pool-accept:{delivery_id}",
        timeout=LOCK_TIMEOUT_S,
        blocking_timeout=LOCK_BLOCKING_S,
    )
    acquired = await lock.acquire()
    if not acquired:
        raise OfferAlreadyTakenError()
    try:
        locked = (
            await session.execute(
                select(Delivery)
                .where(Delivery.id == delivery_id, Delivery.area_id == area_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if locked is None:
            raise NotOfferTargetError()
        if locked.state != "SEM_RESPOSTA":
            raise OfferAlreadyTakenError()
        try:
            locked.courier_id = courier_id
            zone_price = await _zone_price_cents(session, courier_id=courier_id, zona_id=locked.zona_id)
            if zone_price is not None:
                locked.price_cents = zone_price
            else:
                pricing_rows = list(
                    (await session.execute(
                        select(CourierPricingTable).where(
                            CourierPricingTable.courier_id == courier_id,
                            CourierPricingTable.area_id == area_id,
                        )
                    )).scalars().all()
                )
                locked.price_cents = effective_price_cents(
                    pricing_rows,
                    dropoff_nbhd_id=locked.dropoff_neighborhood_id,
                    distance_m=locked.distance_m,
                )
            await transition(
                session,
                delivery=locked,
                to_state="ACEITA",
                actor_id=actor_user_id,
                ip=ip,
            )
        except InvalidTransitionError as exc:
            raise OfferAlreadyTakenError() from exc

        # Defensive cleanup — the pool delivery should have no live Redis state
        # (the cascade clears it before pooling), but never leave a stray key.
        await offer_state.close_offer(r, delivery_id)
        await offer_state.clear_candidates(r, delivery_id)

        logger.info(
            "dispatch.pool.self_assigned",
            area_id=area_id,
            delivery_id=delivery_id,
            courier_id=courier_id,
        )
        return locked
    finally:
        try:
            await lock.release()
        except Exception:  # noqa: BLE001 — lock may have expired; safe to ignore
            pass
