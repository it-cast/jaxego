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

from app.deliveries.models import Delivery
from app.deliveries.service import transition
from app.deliveries.state_machine import InvalidTransitionError
from app.dispatch import offer_state
from app.dispatch.exceptions import NotOfferTargetError, OfferAlreadyTakenError
from app.dispatch.schemas import OfferOut
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood

logger = structlog.get_logger("dispatch.service")

# Accept lock window: the lock auto-expires after `LOCK_TIMEOUT_S` (so a crashed
# holder cannot wedge the row forever); a contender waits at most
# `LOCK_BLOCKING_S` to acquire before treating the offer as taken (TH-1).
LOCK_TIMEOUT_S = 10
LOCK_BLOCKING_S = 2


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

    return OfferOut(
        delivery_id=delivery.id,
        loja_nome=merchant.trade_name if merchant else "",
        pickup_address=delivery.pickup_address,
        pickup_neighborhood=delivery.pickup_neighborhood,
        # RN-013 — neighborhood name + distance ONLY (no street/number/complement).
        dropoff_neighborhood=nbhd.name if nbhd else "",
        distance_m=delivery.distance_m,
        value_cents=delivery.estimate_max_cents,
        payment_method=delivery.payment_method,
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
            locked.courier_id = courier_id  # bind the winner before the transition
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

        # KPI NORTE (observability) — tempo criação→aceite, no PII.
        elapsed_ms: int | None = None
        if locked.created_at is not None and locked.accepted_at is not None:
            elapsed_ms = int((locked.accepted_at - locked.created_at).total_seconds() * 1000)
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
