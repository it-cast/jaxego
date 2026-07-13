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

from app.couriers.models import Courier, CourierPricingTable, CourierZona
from app.deliveries.estimate import effective_price_cents
from app.deliveries.models import Delivery
from app.dispatch import offer_state
from app.dispatch.ranking import rank_key
from app.integrations.routing_stub import haversine_m
from app.merchants.models import Merchant, MerchantCourierBlock, MerchantCourierFavorite
from app.teams.models import TeamZona

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
    zona_id: int | None = None,
    team_ids: list[int] | None = None,
    excluded_ids: set[int] | None = None,
    merchant_lat: float | None = None,
    merchant_lng: float | None = None,
    area_max_concurrent: int = 1,
) -> list[int]:
    """Ordered candidate courier ids: favorites first, then ranking (RN-009).

    Eligible = online + active + not deleted + in team (if specified) +
    load < area_max_concurrent (from AreaConfig, not per-courier) +
    NOT blocked by the store + NOT in excluded_ids. Coverage by neighborhood is no
    longer required — zone pricing determines eligibility. Bulk-loads all pricing
    data (no N+1).
    """
    # Blocked set — removed BEFORE favorites/ranking (TH-5).
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
        (await session.execute(select(Courier).where(*courier_filter))).scalars().all()
    )
    if not couriers:
        return []

    courier_ids = [c.id for c in couriers]
    load_by = await _active_delivery_counts(session, area_id=area_id, courier_ids=courier_ids)

    # Zone pricing maps (bulk, no N+1): courier override → team minimum.
    # `zona_inactive` holds couriers who explicitly opted out of this zone (ativo=False).
    # Couriers with NO override row inherit the team's zone price (tz_map) — but
    # if the TEAM never configured a price for this zone either, the courier is
    # NOT eligible here (see loop below): a zone without preço mínimo do time
    # must stay disabled, not silently fall back to the old pricing table.
    cz_map: dict[int, int] = {}
    zona_inactive: set[int] = set()
    tz_map: dict[int, int] = {}
    if zona_id is not None:
        for cz in (await session.execute(
            select(CourierZona).where(
                CourierZona.zona_id == zona_id,
                CourierZona.courier_id.in_(courier_ids),
            )
        )).scalars():
            if not cz.ativo:
                zona_inactive.add(cz.courier_id)
            else:
                cz_map[cz.courier_id] = cz.preco_cents
        team_ids_set = {c.team_id for c in couriers if c.team_id is not None}
        if team_ids_set:
            tz_map = {
                tz.team_id: tz.preco_minimo_cents
                for tz in (await session.execute(
                    select(TeamZona).where(
                        TeamZona.zona_id == zona_id,
                        TeamZona.team_id.in_(team_ids_set),
                    )
                )).scalars()
            }

    # Old pricing table as final fallback (backward compat).
    pricing_rows = list(
        (await session.execute(
            select(CourierPricingTable).where(
                CourierPricingTable.area_id == area_id,
                CourierPricingTable.courier_id.in_(courier_ids),
            )
        )).scalars().all()
    )
    pricing_by: dict[int, list[CourierPricingTable]] = {}
    for row in pricing_rows:
        pricing_by.setdefault(row.courier_id, []).append(row)

    favorites: list[tuple[int, int]] = []  # (priority, courier_id)
    ranked: list[tuple[tuple, int]] = []   # (rank_key, courier_id)
    _excluded = excluded_ids or set()
    for courier in couriers:
        if courier.id in blocked or courier.id in _excluded:
            continue
        if courier.id in zona_inactive:
            continue  # courier opted out of this zone
        load = load_by.get(courier.id, 0)
        if load >= area_max_concurrent:
            continue  # at/over capacity
        # Zone price first; fall back to old neighborhood/distance table.
        if courier.id in cz_map:
            price: int | None = cz_map[courier.id]
        elif courier.team_id is not None and courier.team_id in tz_map:
            price = tz_map[courier.team_id]
        elif zona_id is not None:
            # Zona sem preço mínimo configurado pelo time (nem override próprio
            # do entregador) → NÃO fica habilitado nessa zona. Sem isso, uma zona
            # recém-criada sem preço liberava todo entregador do time nela.
            continue
        else:
            price = effective_price_cents(
                pricing_by.get(courier.id, []),
                dropoff_nbhd_id=dropoff_nbhd_id,
                distance_m=distance_m,
            )
        rank_price = price if price is not None else 0
        if courier.id in favorite_priority:
            favorites.append((favorite_priority[courier.id], courier.id))
        else:
            # Use real courier→merchant haversine when both positions are known.
            if (
                merchant_lat is not None
                and merchant_lng is not None
                and courier.lat is not None
                and courier.lng is not None
            ):
                eta_s = haversine_m(
                    (float(courier.lat), float(courier.lng)),
                    (merchant_lat, merchant_lng),
                )
            else:
                eta_s = distance_m if distance_m is not None else 0
            key = rank_key(eta_s=eta_s, load=load, price_cents=rank_price, score=0.0)
            ranked.append((key, courier.id))

    favorites.sort(key=lambda t: (t[0], t[1]))
    ranked.sort(key=lambda t: (t[0], t[1]))
    ordered = [cid for _, cid in favorites] + [cid for _, cid in ranked]
    logger.info(
        "dispatch.candidates.built",
        area_id=area_id,
        zona_id=zona_id,
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
        await offer_state.add_declined(r, delivery_id, declined_by)
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
