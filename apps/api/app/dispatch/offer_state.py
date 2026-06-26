"""Redis offer state — the TTL is the source of truth of the timer (ADR-104).

`offer:{delivery_id}` holds the CURRENT offer (target courier + deadline) with a
Redis TTL = the area's `timeout_oferta_s`. The Redis EXPIRE is the event that ends
the offer window — the app's countdown is cosmetic and NEVER decides expiration.

`dispatch:{delivery_id}:candidates` is the ordered candidate queue (favorites
first, then ranking — built once by the cascade). The cascade pops the next
candidate on open; advance is idempotent by COMPARE-AND-ADVANCE (a decline only
advances if `offer:{id}` still points at that candidate — Pitfall 3).

All timestamps are aware UTC (`datetime.now(UTC)` — TD-010).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis


def _offer_key(delivery_id: int) -> str:
    return f"offer:{delivery_id}"


def _candidates_key(delivery_id: int) -> str:
    return f"dispatch:{delivery_id}:candidates"


def _courier_offer_key(courier_id: int) -> str:
    """Reverse index: which delivery is currently offered to this courier."""
    return f"courier_offer:{courier_id}"


# ---------------------------------------------------------------------------
# Current offer — TTL is the source of truth (ADR-104).
# ---------------------------------------------------------------------------
async def open_offer(
    r: aioredis.Redis, *, delivery_id: int, courier_id: int, timeout_s: int
) -> datetime:
    """Open the current offer for `courier_id`; Redis TTL = the timer (ADR-104).

    Returns the aware-UTC deadline (TD-010). The key expires atomically at the end
    of the window, so the offer ends even if the worker restarts (TH-8).
    """
    now = datetime.now(UTC)  # AWARE — TD-010
    expires_at = now + timedelta(seconds=timeout_s)
    payload = json.dumps(
        {
            "courier_id": courier_id,
            "opened_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "timeout_s": timeout_s,
        }
    )
    await r.set(_offer_key(delivery_id), payload, ex=timeout_s)
    # Reverse index so the courier's poll (GET /offers/active) finds its offer; the
    # same TTL expires it in lockstep with the offer itself (ADR-104).
    await r.set(_courier_offer_key(courier_id), str(delivery_id), ex=timeout_s)
    return expires_at


async def current_offer(r: aioredis.Redis, delivery_id: int) -> dict | None:
    """The current offer, or None if it already expired (Redis TTL decided)."""
    raw = await r.get(_offer_key(delivery_id))
    return json.loads(raw) if raw else None


async def active_offer_for_courier(r: aioredis.Redis, courier_id: int) -> int | None:
    """The delivery currently offered to this courier (poll), or None.

    Cross-checks the forward index: the reverse key may outlive a closed offer in
    rare races, so we confirm `offer:{id}` still targets this courier.
    """
    raw = await r.get(_courier_offer_key(courier_id))
    if raw is None:
        return None
    delivery_id = int(raw)
    offer = await current_offer(r, delivery_id)
    if offer is None or offer.get("courier_id") != courier_id:
        return None
    return delivery_id


async def offer_ttl_remaining_s(r: aioredis.Redis, delivery_id: int) -> int | None:
    """Seconds remaining on the offer per Redis (the authoritative timer)."""
    ttl: int = await r.ttl(_offer_key(delivery_id))  # type: ignore[misc]
    # redis: -2 = no key, -1 = no expire. Treat both as "no live offer".
    return ttl if ttl >= 0 else None


async def close_offer(r: aioredis.Redis, delivery_id: int) -> None:
    """Close the current offer (accepted / cancelled). Idempotent.

    Clears both the forward key and the courier reverse index so a stale poll
    cannot resurrect a closed offer.
    """
    offer = await current_offer(r, delivery_id)
    await r.delete(_offer_key(delivery_id))
    if offer is not None:
        courier_id = offer.get("courier_id")
        if isinstance(courier_id, int):
            await r.delete(_courier_offer_key(courier_id))


# ---------------------------------------------------------------------------
# Candidate queue — ordered, popped one at a time (RN-009 — never broadcast).
# ---------------------------------------------------------------------------
async def set_candidates(
    r: aioredis.Redis, *, delivery_id: int, courier_ids: list[int], ttl_s: int
) -> None:
    """Store the ordered candidate queue (favorites first, then ranking)."""
    key = _candidates_key(delivery_id)
    await r.delete(key)
    if courier_ids:
        await r.rpush(key, *[str(c) for c in courier_ids])  # type: ignore[misc]
        await r.expire(key, ttl_s)


async def next_candidate(r: aioredis.Redis, delivery_id: int) -> int | None:
    """Pop the next candidate (FIFO), or None when the queue is exhausted (E1)."""
    raw: str | None = await r.lpop(_candidates_key(delivery_id))  # type: ignore[misc]
    return int(raw) if raw is not None else None


async def clear_candidates(r: aioredis.Redis, delivery_id: int) -> None:
    """Drop the candidate queue (cancel / done)."""
    await r.delete(_candidates_key(delivery_id))


def _declined_key(delivery_id: int) -> str:
    return f"dispatch:{delivery_id}:declined"


async def add_declined(r: aioredis.Redis, delivery_id: int, courier_id: int) -> None:
    """Track a courier who declined this delivery."""
    key = _declined_key(delivery_id)
    await r.sadd(key, str(courier_id))  # type: ignore[misc]
    await r.expire(key, 86400)


async def get_declined(r: aioredis.Redis, delivery_id: int) -> set[int]:
    """Get all courier IDs who declined this delivery."""
    raw = await r.smembers(_declined_key(delivery_id))  # type: ignore[misc]
    return {int(x) for x in raw} if raw else set()


async def clear_declined(r: aioredis.Redis, delivery_id: int) -> None:
    """Clear the declined set (delivery finished)."""
    await r.delete(_declined_key(delivery_id))
