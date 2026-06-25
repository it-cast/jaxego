"""Freight estimate = MEDIAN of eligible online couriers (RN-030 / D-05 / LOW-2).

The estimate shown to the store BEFORE confirming is the median of the effective
prices of the online, eligible couriers for THIS trip. Eligibility (coverage at
both pickup and dropoff) reuses `couriers.coverage.is_eligible` (Phase 6); the
spatial point-in-polygon resolution reuses `neighborhoods.spatial` (Phase 6).

LOW-2 — the "price for the trip" of a single courier depends on the table mode:
  - mode 'neighborhood': the row whose `neighborhood_id` == the dropoff neighborhood.
  - mode 'km': the smallest band whose `up_to_km` >= the trip distance.
A courier with no matching row contributes no price (excluded from the median).

Money is integer cents throughout (never Float) — `median_cents` returns integer
cents or None when there are zero eligible prices (E2 / D-06).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.coverage import is_eligible
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable

logger = structlog.get_logger("deliveries.estimate")


def _to_cents(value: Decimal) -> int:
    """Convert a Decimal reais value to integer cents (no float)."""
    return int((value * 100).quantize(Decimal("1")))


def median_cents(prices: Sequence[int]) -> int | None:
    """Median of integer-cent prices; None if empty (E2 — D-06)."""
    if not prices:
        return None
    s = sorted(prices)
    n = len(s)
    m = n // 2
    if n % 2:
        return s[m]
    return (s[m - 1] + s[m]) // 2  # integer cents


def effective_price_cents(
    rows: Iterable[CourierPricingTable], *, dropoff_nbhd_id: int, distance_m: int | None
) -> int | None:
    """The courier's effective price (cents) for THIS trip (LOW-2), or None.

    mode 'neighborhood' → the row matching the dropoff neighborhood.
    mode 'km' → the smallest band whose `up_to_km` covers the trip distance.
    """
    km_bands: list[tuple[Decimal, Decimal]] = []
    for row in rows:
        if row.mode == "neighborhood":
            if row.neighborhood_id == dropoff_nbhd_id:
                return _to_cents(row.price)
        elif row.mode == "km" and row.up_to_km is not None:
            km_bands.append((row.up_to_km, row.price))

    if km_bands and distance_m is not None:
        distance_km = Decimal(distance_m) / Decimal(1000)
        # Smallest band whose ceiling covers the distance.
        eligible = sorted((b for b in km_bands if b[0] >= distance_km), key=lambda b: b[0])
        if eligible:
            return _to_cents(eligible[0][1])
    return None


async def eligible_online_prices_cents(
    session: AsyncSession,
    *,
    area_id: int,
    pickup_nbhd_id: int,
    dropoff_nbhd_id: int,
    distance_m: int | None,
    team_ids: list[int] | None = None,
) -> list[int]:
    """Effective prices (cents) of online, active, eligible couriers for the trip.

    Reuses `is_eligible` (coverage at BOTH points — Phase 6). Loads each online
    active courier's coverage + pricing rows; a courier contributes a price only
    if eligible AND has a matching pricing row for the trip. Single set of queries
    over the area's online couriers (no N+1 over a large table — the online,
    active set is small).
    """
    filters = [
        Courier.area_id == area_id,
        Courier.is_online.is_(True),
        Courier.status == "active",
        Courier.deleted_at.is_(None),
    ]
    if team_ids:
        filters.append(Courier.team_id.in_(team_ids))
    couriers = list(
        (await session.execute(select(Courier).where(*filters))).scalars().all()
    )
    if not couriers:
        return []

    courier_ids = [c.id for c in couriers]
    coverage_rows = list(
        (
            await session.execute(
                select(CourierCoverageArea).where(
                    CourierCoverageArea.area_id == area_id,
                    CourierCoverageArea.courier_id.in_(courier_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    pricing_rows = list(
        (
            await session.execute(
                select(CourierPricingTable).where(
                    CourierPricingTable.area_id == area_id,
                    CourierPricingTable.courier_id.in_(courier_ids),
                )
            )
        )
        .scalars()
        .all()
    )

    coverage_by_courier: dict[int, list[CourierCoverageArea]] = {}
    for row in coverage_rows:
        coverage_by_courier.setdefault(row.courier_id, []).append(row)
    pricing_by_courier: dict[int, list[CourierPricingTable]] = {}
    for row in pricing_rows:
        pricing_by_courier.setdefault(row.courier_id, []).append(row)

    prices: list[int] = []
    for courier in couriers:
        coverage = coverage_by_courier.get(courier.id, [])
        if not is_eligible(coverage, pickup_nbhd_id, dropoff_nbhd_id):
            continue
        price = effective_price_cents(
            pricing_by_courier.get(courier.id, []),
            dropoff_nbhd_id=dropoff_nbhd_id,
            distance_m=distance_m,
        )
        if price is not None:
            prices.append(price)
    return prices
