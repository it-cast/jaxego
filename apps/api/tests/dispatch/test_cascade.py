"""Cascade advance + exhaustion (REQ-024 / E1).

The worker `advance_offer` opens the next candidate; when the queue is exhausted it
returns False (E1 — the store is notified with the 3 options in the UI). Uses
fakeredis (non-concurrent path).
"""

from __future__ import annotations

from app.dispatch import offer_state
from app.workers.dispatch import advance_offer

from tests.dispatch.conftest import DispatchSeed


async def test_advance_opens_next_then_exhausts(
    dispatch_seed: DispatchSeed, session_factory, fake_redis
) -> None:
    seed = dispatch_seed
    await offer_state.set_candidates(
        fake_redis,
        delivery_id=seed.delivery_id,
        courier_ids=[seed.favorite_courier_id, seed.plain_courier_id],
        ttl_s=120,
    )

    async with session_factory() as s:
        # First advance → favorite gets the offer.
        opened1 = await advance_offer(
            s, fake_redis, area_id=seed.area_id, delivery_id=seed.delivery_id
        )
    assert opened1 is True
    offer = await offer_state.current_offer(fake_redis, seed.delivery_id)
    assert offer is not None
    assert offer["courier_id"] == seed.favorite_courier_id

    # Simulate the TTL expiring (key gone) and advance again → plain courier.
    await fake_redis.delete(f"offer:{seed.delivery_id}")
    async with session_factory() as s:
        opened2 = await advance_offer(
            s, fake_redis, area_id=seed.area_id, delivery_id=seed.delivery_id
        )
    assert opened2 is True
    offer = await offer_state.current_offer(fake_redis, seed.delivery_id)
    assert offer is not None
    assert offer["courier_id"] == seed.plain_courier_id

    # Exhaust → E1.
    await fake_redis.delete(f"offer:{seed.delivery_id}")
    async with session_factory() as s:
        opened3 = await advance_offer(
            s, fake_redis, area_id=seed.area_id, delivery_id=seed.delivery_id
        )
    assert opened3 is False  # cascade exhausted (E1)
    assert await offer_state.current_offer(fake_redis, seed.delivery_id) is None


async def test_advance_stops_when_delivery_not_criada(
    dispatch_seed: DispatchSeed, session_factory, fake_redis
) -> None:
    """If the delivery already left CRIADA, the cascade does not open a new offer."""
    seed = dispatch_seed
    from app.deliveries.models import Delivery

    await offer_state.set_candidates(
        fake_redis,
        delivery_id=seed.delivery_id,
        courier_ids=[seed.favorite_courier_id],
        ttl_s=120,
    )
    async with session_factory() as s:
        delivery = await s.get(Delivery, seed.delivery_id)
        assert delivery is not None
        delivery.state = "CANCELADA"
        await s.commit()

    async with session_factory() as s:
        opened = await advance_offer(
            s, fake_redis, area_id=seed.area_id, delivery_id=seed.delivery_id
        )
    assert opened is False
    assert await offer_state.current_offer(fake_redis, seed.delivery_id) is None
