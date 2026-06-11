"""Accept — happy path + idempotency (non-concurrent, fakeredis + SQLite).

The TRUE 2-accept race (FOR UPDATE + real Redis lock) is `test_accept_race.py`,
marked `@pytest.mark.mysql`. Here the single-threaded path proves: a valid accept
moves CRIADA → ACEITA and binds the courier; a SECOND accept on the now-ACEITA
delivery raises OfferAlreadyTakenError (409) with ZERO penalty (F-05 E3 — the
delivery is not re-cancelled, no extra transition recorded for the loser).
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.dispatch import offer_state
from app.dispatch.exceptions import NotOfferTargetError, OfferAlreadyTakenError
from app.dispatch.service import accept_offer
from sqlalchemy import func, select

from tests.dispatch.conftest import DispatchSeed


async def test_accept_moves_to_aceita_and_binds_courier(
    dispatch_seed: DispatchSeed, session_factory, fake_redis
) -> None:
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    async with session_factory() as s:
        delivery = await accept_offer(
            s,
            fake_redis,
            area_id=seed.area_id,
            delivery_id=seed.delivery_id,
            courier_id=seed.favorite_courier_id,
            actor_user_id=seed.favorite_user_id,
            ip="127.0.0.1",
        )
        await s.commit()
        assert delivery.state == "ACEITA"
        assert delivery.courier_id == seed.favorite_courier_id
        assert delivery.accepted_at is not None

    # The offer + reverse index are closed.
    assert await offer_state.current_offer(fake_redis, seed.delivery_id) is None
    assert await offer_state.active_offer_for_courier(fake_redis, seed.favorite_courier_id) is None


async def test_non_target_courier_gets_404(
    dispatch_seed: DispatchSeed, session_factory, fake_redis
) -> None:
    """A courier who is NOT the offer target gets 404 (A01 / TH-4), not 403."""
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    async with session_factory() as s:
        with pytest.raises(NotOfferTargetError):
            await accept_offer(
                s,
                fake_redis,
                area_id=seed.area_id,
                delivery_id=seed.delivery_id,
                courier_id=seed.plain_courier_id,  # not the target
                actor_user_id=seed.plain_user_id,
                ip=None,
            )


async def test_second_accept_409_without_penalty(
    dispatch_seed: DispatchSeed, session_factory, fake_redis
) -> None:
    """The loser of the race gets 409 and the delivery is NOT re-cancelled (F-05 E3)."""
    seed = dispatch_seed
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.favorite_courier_id, timeout_s=20
    )
    # First accept wins.
    async with session_factory() as s:
        await accept_offer(
            s,
            fake_redis,
            area_id=seed.area_id,
            delivery_id=seed.delivery_id,
            courier_id=seed.favorite_courier_id,
            actor_user_id=seed.favorite_user_id,
            ip=None,
        )
        await s.commit()

    # Re-open an offer to the plain courier (simulating a stale offer) and accept:
    # the delivery is already ACEITA, so the machine rejects → 409, no penalty.
    await offer_state.open_offer(
        fake_redis, delivery_id=seed.delivery_id, courier_id=seed.plain_courier_id, timeout_s=20
    )
    async with session_factory() as s:
        with pytest.raises(OfferAlreadyTakenError):
            await accept_offer(
                s,
                fake_redis,
                area_id=seed.area_id,
                delivery_id=seed.delivery_id,
                courier_id=seed.plain_courier_id,
                actor_user_id=seed.plain_user_id,
                ip=None,
            )

    # No penalty: state is still ACEITA, exactly ONE accept transition, the winner
    # is unchanged, and NO cancellation was recorded for the loser.
    async with session_factory() as s:
        delivery = await s.get(Delivery, seed.delivery_id)
        assert delivery is not None
        assert delivery.state == "ACEITA"
        assert delivery.courier_id == seed.favorite_courier_id
        assert delivery.cancelled_at is None
        accept_count = (
            await s.execute(
                select(func.count(DeliveryStateTransition.id)).where(
                    DeliveryStateTransition.delivery_id == seed.delivery_id,
                    DeliveryStateTransition.to_state == "ACEITA",
                )
            )
        ).scalar_one()
        assert accept_count == 1  # the loser added no transition (no penalty)
        cancel_count = (
            await s.execute(
                select(func.count(DeliveryStateTransition.id)).where(
                    DeliveryStateTransition.delivery_id == seed.delivery_id,
                    DeliveryStateTransition.to_state == "CANCELADA",
                )
            )
        ).scalar_one()
        assert cancel_count == 0  # the loser was NOT treated as a cancel
