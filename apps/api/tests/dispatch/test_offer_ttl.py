"""Redis TTL is the source of truth of the timer (ADR-104).

The offer expires by the Redis EXPIRE; `current_offer` returns None once the key
is gone; the advance moves to the next candidate. The app countdown is cosmetic.
"""

from __future__ import annotations

from app.dispatch import offer_state

from tests.dispatch.conftest import DispatchSeed


async def test_offer_ttl_remaining_from_redis(dispatch_seed: DispatchSeed, fake_redis) -> None:
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    remaining = await offer_state.offer_ttl_remaining_s(fake_redis, seed.delivery_id)
    assert remaining is not None
    assert 0 < remaining <= 20


async def test_offer_expires_when_key_deleted(dispatch_seed: DispatchSeed, fake_redis) -> None:
    """Simulate the TTL boundary by deleting the key — the offer is then gone."""
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    assert await offer_state.current_offer(fake_redis, seed.delivery_id) is not None
    # The Redis EXPIRE firing == the key gone (ADR-104).
    await fake_redis.delete(f"offer:{seed.delivery_id}")
    assert await offer_state.current_offer(fake_redis, seed.delivery_id) is None
    assert await offer_state.offer_ttl_remaining_s(fake_redis, seed.delivery_id) is None


async def test_candidate_queue_pops_in_order(dispatch_seed: DispatchSeed, fake_redis) -> None:
    seed = dispatch_seed
    await offer_state.set_candidates(
        fake_redis,
        delivery_id=seed.delivery_id,
        courier_ids=[seed.favorite_courier_id, seed.plain_courier_id],
        ttl_s=120,
    )
    first = await offer_state.next_candidate(fake_redis, seed.delivery_id)
    second = await offer_state.next_candidate(fake_redis, seed.delivery_id)
    third = await offer_state.next_candidate(fake_redis, seed.delivery_id)
    assert first == seed.favorite_courier_id
    assert second == seed.plain_courier_id
    assert third is None  # exhausted (E1)


async def test_active_offer_reverse_index(dispatch_seed: DispatchSeed, fake_redis) -> None:
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    found = await offer_state.active_offer_for_courier(fake_redis, seed.favorite_courier_id)
    assert found == seed.delivery_id
    # A different courier has no active offer.
    assert await offer_state.active_offer_for_courier(fake_redis, seed.plain_courier_id) is None
    # Closing clears the reverse index too.
    await offer_state.close_offer(fake_redis, seed.delivery_id)
    assert await offer_state.active_offer_for_courier(fake_redis, seed.favorite_courier_id) is None
