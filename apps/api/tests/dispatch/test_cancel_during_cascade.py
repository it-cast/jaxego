"""Store cancels during the cascade (E4 / RN-004) — offers cancelled, zero cost.

`cancel_pending_offers` drops the live offer + candidate queue; a courier holding
the offer then falls into "expired" on their next poll.
"""

from __future__ import annotations

from app.dispatch import offer_state
from app.dispatch.service import cancel_pending_offers

from tests.dispatch.conftest import DispatchSeed


async def test_cancel_clears_offer_and_queue(dispatch_seed: DispatchSeed, fake_redis) -> None:
    seed = dispatch_seed
    await offer_state.set_candidates(
        fake_redis,
        delivery_id=seed.delivery_id,
        courier_ids=[seed.favorite_courier_id, seed.plain_courier_id],
        ttl_s=120,
    )
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    # The courier currently sees the offer.
    assert (
        await offer_state.active_offer_for_courier(fake_redis, seed.favorite_courier_id)
        == seed.delivery_id
    )

    # E4: store cancels → all dispatch state for the delivery is gone (zero cost).
    await cancel_pending_offers(fake_redis, delivery_id=seed.delivery_id)

    assert await offer_state.current_offer(fake_redis, seed.delivery_id) is None
    assert await offer_state.next_candidate(fake_redis, seed.delivery_id) is None
    # The courier's poll now finds nothing → "expired" in the UI.
    assert await offer_state.active_offer_for_courier(fake_redis, seed.favorite_courier_id) is None
