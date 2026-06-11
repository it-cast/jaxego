"""Haversine fallback + SQLite within_radius (A1 fallback — DB-free, not-mysql).

The spatial check itself runs in MySQL (test_geofence_db.py, @pytest.mark.mysql);
here we pin the Python reference so the geofence has a deterministic, network-free
ground truth and the SQLite path (dev) agrees with it. A known pair (~111m apart in
latitude) exercises inside/outside the radius and proves the axis order is right
(a swapped lat/lng would give thousands of km — Pitfall 4).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from app.proofs.geofence import distance_m, haversine_m, within_radius
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Pádua-ish reference. 0.001° of latitude ≈ 111.2 m.
PICKUP_LAT, PICKUP_LNG = -21.5400, -42.1800
NEAR_LAT, NEAR_LNG = -21.5405, -42.1800  # ~55 m south
FAR_LAT, FAR_LNG = -21.5500, -42.1800  # ~1.11 km south


def test_haversine_known_pair_metres() -> None:
    """0.001° latitude ≈ 111 m — proves unit (metres) and axis order."""
    d = haversine_m(PICKUP_LAT, PICKUP_LNG, PICKUP_LAT - 0.001, PICKUP_LNG)
    assert 110.0 <= d <= 113.0


def test_haversine_zero_distance() -> None:
    assert haversine_m(PICKUP_LAT, PICKUP_LNG, PICKUP_LAT, PICKUP_LNG) == pytest.approx(0.0)


def test_haversine_not_thousands_of_km_for_close_points() -> None:
    """A swapped lat/lng (Pitfall 4) would yield a huge distance — guard against it."""
    d = haversine_m(NEAR_LAT, NEAR_LNG, PICKUP_LAT, PICKUP_LNG)
    assert d < 200.0  # close points stay close


@pytest_asyncio.fixture
async def session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncSession:
    async with session_factory() as s:
        yield s


@pytest.mark.asyncio
async def test_within_radius_inside_sqlite_fallback(session: AsyncSession) -> None:
    """SQLite path falls back to haversine: ~55 m point is inside an 80 m radius."""
    assert await within_radius(
        session,
        lat=NEAR_LAT,
        lng=NEAR_LNG,
        target_lat=PICKUP_LAT,
        target_lng=PICKUP_LNG,
        radius_m=80,
    )


@pytest.mark.asyncio
async def test_within_radius_outside_sqlite_fallback(session: AsyncSession) -> None:
    """~1.11 km point is outside an 80 m radius — rejected."""
    assert not await within_radius(
        session,
        lat=FAR_LAT,
        lng=FAR_LNG,
        target_lat=PICKUP_LAT,
        target_lng=PICKUP_LNG,
        radius_m=80,
    )


@pytest.mark.asyncio
async def test_distance_m_sqlite_matches_haversine(session: AsyncSession) -> None:
    db = await distance_m(
        session, lat=NEAR_LAT, lng=NEAR_LNG, target_lat=PICKUP_LAT, target_lng=PICKUP_LNG
    )
    py = haversine_m(NEAR_LAT, NEAR_LNG, PICKUP_LAT, PICKUP_LNG)
    assert db == pytest.approx(py)
