"""ST_Distance_Sphere against LIVE MySQL 8 — SRID/axis/unit (A1, @pytest.mark.mysql).

This is the ROADMAP acceptance criterion for the geofence: a point INSIDE the radius
of a known target passes; a point OUTSIDE is rejected; and the returned distance is
PLAUSIBLE metres (not thousands of km — Pitfall 4 proves POINT(lng,lat) axis order).
Skipped in dev via `-m "not mysql"`; SQLite has no ST_Distance_Sphere. Run live:

    cd apps/api && uv run pytest -m mysql tests/proofs/test_geofence_db.py

Connection lifecycle mirrors tests/deliveries/test_append_only.py: a DEDICATED async
engine on `settings.database_url` + NullPool, disposed inside the test loop, so no
pooled aiomysql connection is finalised against a closed loop on Windows. No schema
seeding is needed — ST_Distance_Sphere is a pure function over POINT literals.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.config import settings
from app.proofs.geofence import distance_m, haversine_m, within_radius
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

pytestmark = pytest.mark.mysql

# Known Pádua-ish pair. 0.001° latitude ≈ 111 m.
TARGET_LAT, TARGET_LNG = -21.5400, -42.1800
NEAR_LAT, NEAR_LNG = -21.5405, -42.1800  # ~55 m
FAR_LAT, FAR_LNG = -21.5500, -42.1800  # ~1.11 km


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncIterator[AsyncEngine]:
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def mysql_session(
    mysql_engine: AsyncEngine,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    yield async_sessionmaker(bind=mysql_engine, expire_on_commit=False, autoflush=False)


@pytest.mark.asyncio
async def test_distance_sphere_returns_plausible_metres(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    """~55 m apart → ST_Distance_Sphere returns ~55 m (NOT thousands of km)."""
    async with mysql_session() as s:
        d = await distance_m(
            s, lat=NEAR_LAT, lng=NEAR_LNG, target_lat=TARGET_LAT, target_lng=TARGET_LNG
        )
    # Agrees with the Python reference within a few metres → axis/unit correct.
    assert d == pytest.approx(haversine_m(NEAR_LAT, NEAR_LNG, TARGET_LAT, TARGET_LNG), abs=5.0)
    assert d < 200.0  # Pitfall 4: a swapped axis would be ~10^6 m


@pytest.mark.asyncio
async def test_within_radius_inside_mysql(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    async with mysql_session() as s:
        assert await within_radius(
            s, lat=NEAR_LAT, lng=NEAR_LNG, target_lat=TARGET_LAT, target_lng=TARGET_LNG, radius_m=80
        )


@pytest.mark.asyncio
async def test_within_radius_outside_mysql(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    async with mysql_session() as s:
        assert not await within_radius(
            s, lat=FAR_LAT, lng=FAR_LNG, target_lat=TARGET_LAT, target_lng=TARGET_LNG, radius_m=80
        )
