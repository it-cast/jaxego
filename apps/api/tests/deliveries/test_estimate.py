"""Freight estimate = MEDIAN of eligible online couriers (REQ-023 / RN-030 / LOW-2).

`median_cents` is a pure helper over integer cents (no float). `effective_price_cents`
resolves a single courier's price for the SPECIFIC trip (per-neighborhood line OR
per-km band — LOW-2). 0 eligible couriers (E2) → None (the create flow turns this
into a non-blocking warning, D-06).
"""

from __future__ import annotations

from decimal import Decimal

from app.couriers.models import CourierPricingTable
from app.deliveries.estimate import effective_price_cents, median_cents


def _row(**kw) -> CourierPricingTable:
    return CourierPricingTable(area_id=1, courier_id=kw.pop("courier_id", 1), **kw)


def test_median_empty_is_none() -> None:
    assert median_cents([]) is None


def test_median_odd() -> None:
    assert median_cents([1000, 1500, 2000]) == 1500


def test_median_even_is_integer_cents() -> None:
    # (1000 + 2000) // 2 — integer cents, never float.
    assert median_cents([1000, 2000]) == 1500
    assert median_cents([1000, 1100]) == 1050


def test_median_unsorted_input() -> None:
    assert median_cents([2000, 1000, 1500]) == 1500


def test_effective_price_neighborhood_mode() -> None:
    rows = [_row(mode="neighborhood", neighborhood_id=7, price=Decimal("12.50"))]
    assert effective_price_cents(rows, dropoff_nbhd_id=7, distance_m=3000) == 1250


def test_effective_price_neighborhood_no_match_is_none() -> None:
    rows = [_row(mode="neighborhood", neighborhood_id=99, price=Decimal("12.50"))]
    assert effective_price_cents(rows, dropoff_nbhd_id=7, distance_m=3000) is None


def test_effective_price_km_band() -> None:
    # 3 km trip: pick the smallest band whose up_to_km >= distance.
    rows = [
        _row(mode="km", up_to_km=Decimal("2.0"), price=Decimal("8.00")),
        _row(mode="km", up_to_km=Decimal("5.0"), price=Decimal("12.00")),
        _row(mode="km", up_to_km=Decimal("10.0"), price=Decimal("18.00")),
    ]
    assert effective_price_cents(rows, dropoff_nbhd_id=7, distance_m=3000) == 1200


def test_effective_price_km_over_max_band_is_none() -> None:
    rows = [_row(mode="km", up_to_km=Decimal("2.0"), price=Decimal("8.00"))]
    # 9 km exceeds the only band — no price for this trip.
    assert effective_price_cents(rows, dropoff_nbhd_id=7, distance_m=9000) is None


def test_median_of_mixed_modes() -> None:
    """LOW-2: one neighborhood courier + one km courier → median of effective prices."""
    nbhd_rows = [_row(courier_id=1, mode="neighborhood", neighborhood_id=7, price=Decimal("10.00"))]
    km_rows = [_row(courier_id=2, mode="km", up_to_km=Decimal("5.0"), price=Decimal("14.00"))]
    p1 = effective_price_cents(nbhd_rows, dropoff_nbhd_id=7, distance_m=3000)
    p2 = effective_price_cents(km_rows, dropoff_nbhd_id=7, distance_m=3000)
    assert p1 == 1000
    assert p2 == 1400
    assert median_cents([p1, p2]) == 1200
