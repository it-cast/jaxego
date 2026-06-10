"""Courier availability online/offline (REQ-018) — SQLite, no live MySQL.

Only a courier with status `active` (KYC ok, Phase 5) may go online; a
non-active courier is rejected with 409. `busy` is DERIVED from the load
(active deliveries vs max_concurrent) via the pure helper `compute_busy` — it is
NOT a persisted editable field.

Imports `app.couriers.availability` lazily via `pytest.importorskip` so the
Wave 0 scaffold COLLECTS before Plan 03 creates the module.
"""

from __future__ import annotations

import pytest


def test_compute_busy_is_derived() -> None:
    """busy = active_deliveries >= max_concurrent (pure, no persistence)."""
    availability = pytest.importorskip("app.couriers.availability")
    assert availability.compute_busy(active_deliveries=0, max_concurrent=1) is False
    assert availability.compute_busy(active_deliveries=1, max_concurrent=1) is True
    assert availability.compute_busy(active_deliveries=2, max_concurrent=3) is False
    assert availability.compute_busy(active_deliveries=3, max_concurrent=3) is True


@pytest.mark.asyncio
async def test_active_courier_can_go_online(db_session, courier_seed) -> None:
    """REQ-018: an active courier may go online (is_online → True)."""
    availability = pytest.importorskip("app.couriers.availability")
    from tests.couriers.conftest import make_courier

    courier = await make_courier(
        db_session,
        area_id=courier_seed["area_a_id"],
        user_id=courier_seed["user_id"],
        status="active",
    )
    updated = await availability.set_availability(
        db_session, area_id=courier.area_id, courier_id=courier.id, online=True
    )
    assert updated.is_online is True


@pytest.mark.asyncio
async def test_non_active_courier_cannot_go_online(db_session, courier_seed) -> None:
    """REQ-018: a pending_kyc courier cannot go online → 409."""
    availability = pytest.importorskip("app.couriers.availability")
    from tests.couriers.conftest import make_courier

    courier = await make_courier(
        db_session,
        area_id=courier_seed["area_a_id"],
        user_id=courier_seed["user_id"],
        status="pending_kyc",
    )
    with pytest.raises(availability.CannotGoOnlineError) as exc:
        await availability.set_availability(
            db_session, area_id=courier.area_id, courier_id=courier.id, online=True
        )
    assert exc.value.status_code == 409
