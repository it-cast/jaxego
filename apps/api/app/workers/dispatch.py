"""Dispatch worker — the re-enqueuable cascade job + push send (LOW-1).

`dispatch_offer_task(delivery_id)` is the entry point (enqueued when a delivery is
created): it builds the candidate queue once, opens the first offer, and re-defers
itself by `timeout_oferta_s + ε`. On each re-run it checks whether the current
offer is still live; if it EXPIRED (Redis TTL decided — ADR-104), it advances to
the next candidate (favorites → ranking → E1 exhausted). The cascade lock
`cascade:{id}` serializes the timeout path with declines (Pitfall 3).

`advance_offer` opens the next candidate (or fires E1 when exhausted).
`send_push_task` sends one Web Push via the adapter; `enqueue_push` puts a send on
the queue. The job NEVER blocks on OSRM/push (TH-8).
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.config_schema import AreaConfig
from app.areas.models import Area
from app.core.redis import get_redis_client
from app.deliveries.models import Delivery
from app.dispatch import cascade, offer_state
from app.integrations.base import PushMessage
from app.integrations.factory import get_push_adapter

logger = structlog.get_logger("workers.dispatch")

# Small slack added to the re-defer so the Redis key has surely expired before the
# job inspects it (avoids racing the TTL boundary).
_DEFER_SLACK_S = 1


async def _area_config(session: AsyncSession, area_id: int) -> AreaConfig:
    """Load the area's typed config (timeouts). Defaults if unset."""
    area = await session.get(Area, area_id)
    raw = dict(area.config) if area and area.config else {}
    try:
        return AreaConfig(**raw)
    except Exception:  # noqa: BLE001 — fall back to defaults rather than wedge dispatch
        return AreaConfig()


async def _open_for_courier(
    session: AsyncSession,
    r: aioredis.Redis,
    *,
    delivery_id: int,
    courier_id: int,
    timeout_s: int,
    ctx: dict[str, Any] | None,
) -> None:
    """Open an offer + enqueue the courier push + re-defer the advance."""
    await offer_state.open_offer(
        r, delivery_id=delivery_id, courier_id=courier_id, timeout_s=timeout_s
    )
    logger.info(
        "dispatch.offer.opened",
        delivery_id=delivery_id,
        courier_id=courier_id,
        timeout_s=timeout_s,
    )
    await enqueue_push(delivery_id=delivery_id, reason="offer", ctx=ctx)
    # Re-defer the cascade so the timeout advances even if no decline arrives.
    if ctx is not None and "redis" in ctx:
        await ctx["redis"].enqueue_job(
            "dispatch_offer_task", delivery_id, _defer_by=timeout_s + _DEFER_SLACK_S
        )


async def advance_offer(
    session: AsyncSession,
    r: aioredis.Redis,
    *,
    area_id: int,
    delivery_id: int,
    ctx: dict[str, Any] | None = None,
) -> bool:
    """Open the next candidate; return False when the queue is exhausted (E1).

    Caller holds the `cascade:{id}` lock (decline) OR runs in the deferred job
    (timeout). Only acts while the delivery is still CRIADA.
    """
    delivery = await session.get(Delivery, delivery_id)
    if delivery is None or delivery.state != "CRIADA":
        await offer_state.clear_candidates(r, delivery_id)
        return False

    cfg = await _area_config(session, area_id)
    courier_id = await offer_state.next_candidate(r, delivery_id)
    if courier_id is None:
        # E1 — cascade exhausted; notify the store (3 options handled in the UI).
        await offer_state.clear_candidates(r, delivery_id)
        logger.info("dispatch.cascade.exhausted", area_id=area_id, delivery_id=delivery_id)
        await enqueue_push(delivery_id=delivery_id, reason="exhausted", ctx=ctx)
        return False

    await _open_for_courier(
        session,
        r,
        delivery_id=delivery_id,
        courier_id=courier_id,
        timeout_s=cfg.timeout_oferta_s,
        ctx=ctx,
    )
    return True


async def dispatch_offer_task(ctx: dict[str, Any], delivery_id: int) -> str:
    """arq entry point — start or advance the cascade for a delivery (LOW-1).

    First run: build the candidate queue and open the first offer. Subsequent runs
    (re-deferred by TTL+ε): if the current offer expired, advance to the next
    candidate. Serialized with declines by the `cascade:{id}` lock (Pitfall 3).
    """
    r = get_redis_client()
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        delivery = await session.get(Delivery, delivery_id)
        if delivery is None or delivery.state != "CRIADA":
            await offer_state.clear_candidates(r, delivery_id)
            return "not-criada"

        lock = r.lock(f"cascade:{delivery_id}", timeout=10, blocking_timeout=2)
        if not await lock.acquire():
            return "locked"
        try:
            current = await offer_state.current_offer(r, delivery_id)
            if current is not None:
                return "offer-live"  # still within the window — nothing to do

            # No live offer: either the very first run, or the TTL just expired.
            cfg = await _area_config(session, delivery.area_id)
            existing = await r.exists(f"dispatch:{delivery_id}:candidates")
            if not existing:
                pickup_id = delivery.dropoff_neighborhood_id  # pickup polygon optional (Phase 7)
                candidates = await cascade.build_candidates(
                    session,
                    area_id=delivery.area_id,
                    merchant_id=delivery.merchant_id,
                    pickup_nbhd_id=pickup_id,
                    dropoff_nbhd_id=delivery.dropoff_neighborhood_id,
                    distance_m=delivery.distance_m,
                )
                # Queue lives for the whole favorites+ranking window.
                ttl = cfg.timeout_oferta_s * (len(candidates) + 1) + cfg.timeout_favoritos_s
                await offer_state.set_candidates(
                    r, delivery_id=delivery_id, courier_ids=candidates, ttl_s=ttl
                )
            opened = await advance_offer(
                session, r, area_id=delivery.area_id, delivery_id=delivery_id, ctx=ctx
            )
            return "opened" if opened else "exhausted"
        finally:
            try:
                await lock.release()
            except Exception:  # noqa: BLE001 — lock may have expired
                pass


# ---------------------------------------------------------------------------
# Push — enqueued, never synchronous (skill push). Payload has ZERO PII (LOW-5).
# ---------------------------------------------------------------------------
async def enqueue_push(*, delivery_id: int, reason: str, ctx: dict[str, Any] | None = None) -> None:
    """Put a push send on the queue (best-effort; degrade silently if no queue)."""
    redis_pool = ctx.get("redis") if ctx else None
    if redis_pool is not None:
        await redis_pool.enqueue_job("send_push_task", delivery_id, reason)
    else:
        logger.info("dispatch.push.enqueue_skipped", delivery_id=delivery_id, reason=reason)


async def enqueue_dispatch(delivery_id: int) -> bool:
    """Enqueue the cascade for a freshly-created delivery (called from the API).

    Opens a short-lived arq pool, enqueues `dispatch_offer_task`, and closes it.
    Best-effort: a failure to enqueue must never break delivery creation (the
    delivery is already persisted; an ops re-enqueue or the next sweep recovers).
    """
    from arq import create_pool
    from arq.connections import RedisSettings

    from app.core.config import settings

    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("dispatch_offer_task", delivery_id)
        finally:
            await pool.aclose()
        return True
    except Exception:  # noqa: BLE001 — never break create on a queue hiccup
        logger.warning("dispatch.enqueue_failed", delivery_id=delivery_id)
        return False


async def send_push_task(ctx: dict[str, Any], delivery_id: int, reason: str) -> str:
    """Send ONE Web Push for a delivery offer/accept (payload has no PII — LOW-5).

    The subscription lookup is a Phase-9 concern (no push_subscriptions table yet);
    M1 sends to a no-op subscription via the Stub adapter and verifies the payload
    shape. The adapter degrades silently on failure (skill push).
    """
    adapter = get_push_adapter()
    message = PushMessage(
        subscription={},  # Phase 9 wires real subscriptions
        delivery_id=delivery_id,
        deep_link=f"/entregador/oferta/{delivery_id}",
        title="Nova oferta",
    )
    ok = await adapter.send(message)
    logger.info("dispatch.push.sent", delivery_id=delivery_id, reason=reason, ok=ok)
    return "sent" if ok else "skipped"
