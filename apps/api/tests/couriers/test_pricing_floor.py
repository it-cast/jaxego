"""Courier pricing floor (RN-015 / REQ-017) — SQLite, no live MySQL.

The platform NEVER fixes the price: it only imposes a floor. A price below the
area floor is rejected with a 422 whose MESSAGE CITES the floor. Mode
`neighborhood` validates `piso_entrega`; mode `km` validates `piso_km`.

Imports `app.couriers.pricing` lazily via `pytest.importorskip` so the Wave 0
scaffold COLLECTS before Plan 03 creates the module.
"""

from __future__ import annotations

import pytest


def test_neighborhood_price_below_floor_rejected_cites_floor() -> None:
    """RN-015: mode 'neighborhood' below piso_entrega → error citing the floor."""
    pricing = pytest.importorskip("app.couriers.pricing")
    with pytest.raises(pricing.PriceBelowFloorError) as exc:
        pricing.assert_above_floor(
            price=5.00,
            floor_km=2.00,
            floor_entrega=8.00,
            mode="neighborhood",
        )
    assert exc.value.status_code == 422
    # The message must cite the floor value (8,00) — RN-015 acceptance.
    assert "8" in exc.value.message
    assert "entrega" in exc.value.message.lower()


def test_km_price_below_floor_rejected_cites_floor() -> None:
    """RN-015: mode 'km' below piso_km → error citing the floor."""
    pricing = pytest.importorskip("app.couriers.pricing")
    with pytest.raises(pricing.PriceBelowFloorError) as exc:
        pricing.assert_above_floor(
            price=1.00,
            floor_km=2.50,
            floor_entrega=8.00,
            mode="km",
        )
    assert exc.value.status_code == 422
    assert "2" in exc.value.message
    assert "km" in exc.value.message.lower()


def test_price_at_or_above_floor_accepted() -> None:
    """A price >= the floor passes (platform never fixes; only floors)."""
    pricing = pytest.importorskip("app.couriers.pricing")
    # Exactly at the floor and above both pass (no exception).
    pricing.assert_above_floor(
        price=8.00, floor_km=2.00, floor_entrega=8.00, mode="neighborhood"
    )
    pricing.assert_above_floor(
        price=3.00, floor_km=2.50, floor_entrega=8.00, mode="km"
    )
