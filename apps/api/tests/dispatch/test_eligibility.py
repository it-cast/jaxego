"""Eligibility / candidate order (REQ-012 / RN-014 / TH-5).

Blocked couriers NEVER appear in `build_candidates`; favorites come first; an
out-of-coverage courier is excluded.
"""

from __future__ import annotations

from app.dispatch.cascade import build_candidates

from tests.dispatch.conftest import DispatchSeed


async def test_blocked_never_in_candidates_and_favorites_first(
    dispatch_seed: DispatchSeed, session_factory
) -> None:
    seed = dispatch_seed
    async with session_factory() as s:
        candidates = await build_candidates(
            s,
            area_id=seed.area_id,
            merchant_id=seed.merchant_id,
            pickup_nbhd_id=seed.pickup_nbhd_id,
            dropoff_nbhd_id=seed.dropoff_nbhd_id,
            distance_m=2800,
        )

    # Blocked never offered (RN-014 / TH-5).
    assert seed.blocked_courier_id not in candidates
    # Out-of-coverage excluded.
    assert seed.uncovered_courier_id not in candidates
    # Favorite + plain are eligible.
    assert seed.favorite_courier_id in candidates
    assert seed.plain_courier_id in candidates
    # Favorite comes FIRST (D-01).
    assert candidates[0] == seed.favorite_courier_id
    assert candidates.index(seed.favorite_courier_id) < candidates.index(seed.plain_courier_id)


async def test_offline_courier_excluded(dispatch_seed: DispatchSeed, session_factory) -> None:
    seed = dispatch_seed
    from app.couriers.models import Courier

    async with session_factory() as s:
        plain = await s.get(Courier, seed.plain_courier_id)
        assert plain is not None
        plain.is_online = False
        await s.commit()

    async with session_factory() as s:
        candidates = await build_candidates(
            s,
            area_id=seed.area_id,
            merchant_id=seed.merchant_id,
            pickup_nbhd_id=seed.pickup_nbhd_id,
            dropoff_nbhd_id=seed.dropoff_nbhd_id,
            distance_m=2800,
        )
    assert seed.plain_courier_id not in candidates
    assert seed.favorite_courier_id in candidates
