"""Cascade candidate build (RN-009) + advance helpers (LOW-1 / Pitfall 3).

`build_candidates` assembles the ordered offer queue for a CRIADA delivery:
online + active + covers BOTH points (reuses `is_eligible`, Phase 6) + load <
max_concurrent + NOT blocked by the store. FAVORITES come first (ordered by their
`priority` — D-01); the rest are ranked by `rank_key` (ETA + load + price — D-02,
score weight 0 in M1). The query loads coverage/pricing/favorites/blocks in BULK
(no N+1 — the estimate.py pattern). It NEVER broadcasts: the queue is consumed one
candidate at a time (RN-009).

`advance_after_decline` / `enqueue_accept_notifications` keep the router free of
worker imports; the actual arq job lives in `app/workers/dispatch.py`.
"""

from __future__ import annotations

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.coverage import is_eligible
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable
from app.deliveries.estimate import effective_price_cents
from app.deliveries.models import Delivery
from app.dispatch import offer_state
from app.dispatch.ranking import rank_key
from app.merchants.models import MerchantCourierBlock, MerchantCourierFavorite

logger = structlog.get_logger("dispatch.cascade")


async def _active_delivery_counts(
    session: AsyncSession, *, area_id: int, courier_ids: list[int]
) -> dict[int, int]:
    """Count each courier's in-flight (ACEITA/COLETADA) deliveries — bulk (no N+1)."""
    if not courier_ids:
        return {}
    rows = (
        await session.execute(
            select(Delivery.courier_id).where(
                Delivery.area_id == area_id,
                Delivery.courier_id.in_(courier_ids),
                Delivery.state.in_(("ACEITA", "COLETADA")),
            )
        )
    ).all()
    counts: dict[int, int] = {}
    for (cid,) in rows:
        if cid is not None:
            counts[cid] = counts.get(cid, 0) + 1
    return counts


async def build_candidates(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    pickup_nbhd_id: int,
    dropoff_nbhd_id: int,
    distance_m: int | None,
    team_ids: list[int] | None = None,
) -> list[int]:
    """Ordered candidate courier ids: favorites first, then ranking (RN-009).

    Eligible = online + active + not deleted + covers BOTH points + load < max +
    NOT blocked by the store. Bulk-loads coverage/pricing/favorites/blocks (no N+1).
    """
    # Blocked set — removed BEFORE favorites/ranking (TH-5). Set difference.
    blocked = {
        cid
        for (cid,) in (
            await session.execute(
                select(MerchantCourierBlock.courier_id).where(
                    MerchantCourierBlock.area_id == area_id,
                    MerchantCourierBlock.merchant_id == merchant_id,
                )
            )
        ).all()
    }
    # Favorites with priority (D-01) — lower priority is offered first.
    favorite_rows = (
        await session.execute(
            select(MerchantCourierFavorite.courier_id, MerchantCourierFavorite.priority).where(
                MerchantCourierFavorite.area_id == area_id,
                MerchantCourierFavorite.merchant_id == merchant_id,
            )
        )
    ).all()
    favorite_priority: dict[int, int] = {int(cid): int(prio) for cid, prio in favorite_rows}

    # Online active couriers in the area (filtered by team if specified).
    courier_filter = [
        Courier.area_id == area_id,
        Courier.is_online.is_(True),
        Courier.status == "active",
        Courier.deleted_at.is_(None),
    ]
    if team_ids:
        courier_filter.append(Courier.team_id.in_(team_ids))
    couriers = list(
        (
            await session.execute(select(Courier).where(*courier_filter))
        )
        .scalars()
        .all()
    )
    if not couriers:
        return []

    courier_ids = [c.id for c in couriers]
    coverage_rows = list(
        (
            await session.execute(
                select(CourierCoverageArea).where(
                    CourierCoverageArea.area_id == area_id,
                    CourierCoverageArea.courier_id.in_(courier_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    pricing_rows = list(
        (
            await session.execute(
                select(CourierPricingTable).where(
                    CourierPricingTable.area_id == area_id,
                    CourierPricingTable.courier_id.in_(courier_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    coverage_by: dict[int, list[CourierCoverageArea]] = {}
    for row in coverage_rows:
        coverage_by.setdefault(row.courier_id, []).append(row)
    pricing_by: dict[int, list[CourierPricingTable]] = {}
    for row in pricing_rows:
        pricing_by.setdefault(row.courier_id, []).append(row)
    load_by = await _active_delivery_counts(session, area_id=area_id, courier_ids=courier_ids)

    favorites: list[tuple[int, int]] = []  # (priority, courier_id)
    ranked: list[tuple[tuple, int]] = []  # (rank_key, courier_id)
    for courier in couriers:
        if courier.id in blocked:
            continue  # blocked never receives an offer (RN-014 / TH-5)
        coverage = coverage_by.get(courier.id, [])
        if not is_eligible(coverage, pickup_nbhd_id, dropoff_nbhd_id):
            continue
        load = load_by.get(courier.id, 0)
        if load >= courier.max_concurrent:
            continue  # at/over capacity
        price = effective_price_cents(
            pricing_by.get(courier.id, []),
            dropoff_nbhd_id=dropoff_nbhd_id,
            distance_m=distance_m,
        )
        if price is None:
            continue  # no price for this trip → cannot offer
        if courier.id in favorite_priority:
            favorites.append((favorite_priority[courier.id], courier.id))
        else:
            # ETA placeholder = distance (OSRM enrichment is M-later); score 0 (ADR-013).
            eta_s = distance_m if distance_m is not None else 0
            key = rank_key(eta_s=eta_s, load=load, price_cents=price, score=0.0)
            ranked.append((key, courier.id))

    favorites.sort(key=lambda t: (t[0], t[1]))
    ranked.sort(key=lambda t: (t[0], t[1]))
    ordered = [cid for _, cid in favorites] + [cid for _, cid in ranked]
    logger.info(
        "dispatch.candidates.built",
        area_id=area_id,
        delivery_id=None,
        favorites=len(favorites),
        ranked=len(ranked),
        blocked=len(blocked),
    )
    return ordered


async def advance_after_decline(
    session: AsyncSession,
    r: aioredis.Redis,
    *,
    area_id: int,
    delivery_id: int,
    declined_by: int,
) -> None:
    """Advance the cascade after a decline — compare-and-advance (Pitfall 3).

    Only advances if the CURRENT offer still targets the decliner; otherwise the
    timeout already moved on (idempotent). Serialized with the timeout path by the
    `cascade:{id}` lock so a decline and a TTL-expire never double-advance.
    """
    from app.workers.dispatch import advance_offer

    lock = r.lock(f"cascade:{delivery_id}", timeout=10, blocking_timeout=2)
    if not await lock.acquire():
        return
    try:
        offer = await offer_state.current_offer(r, delivery_id)
        if offer is None or offer.get("courier_id") != declined_by:
            return  # the offer already moved on — nothing to do (idempotent)
        await offer_state.close_offer(r, delivery_id)
        logger.info(
            "dispatch.offer.declined",
            area_id=area_id,
            delivery_id=delivery_id,
            courier_id=declined_by,
        )
        await advance_offer(session, r, area_id=area_id, delivery_id=delivery_id)
    finally:
        try:
            await lock.release()
        except Exception:  # noqa: BLE001 — lock may have expired
            pass


async def enqueue_accept_notifications(*, delivery_id: int) -> None:
    """Enqueue the store/recipient push after an accept (never synchronous)."""
    from app.workers.dispatch import enqueue_push

    await enqueue_push(delivery_id=delivery_id, reason="accepted")
