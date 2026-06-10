"""Point-in-polygon eligibility (REQ-003) — asserts against LIVE MySQL 8.

This exercises `app.neighborhoods.spatial.point_in_polygon` (ST_Contains) against
a real MySQL 8 server: a point INSIDE the seeded polygon is eligible; a point
OUTSIDE is not. Marked `@pytest.mark.mysql` (skipped in dev via `-m "not mysql"`,
run live with `-m mysql`) — SQLite has no spatial functions. This is the ROADMAP
acceptance criterion (ponto dentro/fora decide elegibilidade).

The polygon is seeded through the REAL project path: `create_neighborhood`
validates the GeoJSON server-side (shapely, anti-DoS) and writes the spatial
column via `ST_GeomFromGeoJSON` — the same code production uses. Each test seeds a
unique-codename area + one catalog row, asserts, then tears down both for
idempotency (a second `-m mysql` run starts clean).

Pitfall 2: GeoJSON is `[lng, lat]`; WKT SRID 4326 is lat-first. The single helper
in spatial.py owns the axis order; the conftest points are (lat, lng) and feed
`point_in_polygon` directly.

Connection lifecycle: a DEDICATED async engine is built and disposed inside the
test's own event loop (`mysql_engine` fixture, NullPool + `await engine.dispose()`
in teardown). The process-wide `app.db.session.engine` pools aiomysql connections
created outside any test loop; when a function-scoped loop closes, the pooled
`aiomysql.Connection.__del__` fires against an already-closed loop and raises
`RuntimeError: Event loop is closed`, which pytest escalates into a spurious
FAILED on Windows. Per-test dispose within the loop avoids that entirely.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.core.config import settings
from app.neighborhoods.schemas import NeighborhoodCreate
from app.neighborhoods.service import create_neighborhood
from app.neighborhoods.spatial import point_in_polygon
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tests.neighborhoods.conftest import (
    PADUA_SQUARE_GEOJSON,
    POINT_INSIDE,
    POINT_OUTSIDE,
)

pytestmark = pytest.mark.mysql


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncIterator[AsyncEngine]:
    """A dedicated async engine created and disposed within the test event loop.

    NullPool keeps no connection alive between checkouts, and the explicit
    `await engine.dispose()` in teardown closes everything inside this loop, so no
    aiomysql connection is ever finalized against a closed loop on Windows.
    """
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
    """Session factory bound to the live MySQL engine (real `mysql` dialect)."""
    yield async_sessionmaker(bind=mysql_engine, expire_on_commit=False, autoflush=False)


async def _seed_area_with_polygon(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[int, int]:
    """Seed a unique-codename Area + one neighborhood with the Pádua polygon.

    Uses the REAL service path (`create_neighborhood` → shapely validation →
    `ST_GeomFromGeoJSON`). Returns (area_id, neighborhood_id).
    """
    codename = f"spatial-test-{uuid.uuid4().hex[:12]}"
    async with factory() as s:
        area = Area(codename=codename, name="Spatial Test", config={})
        s.add(area)
        await s.flush()
        nbhd, status = await create_neighborhood(
            s,
            area_id=area.id,
            body=NeighborhoodCreate(name="Centro", polygon_geojson=PADUA_SQUARE_GEOJSON),
        )
        # Sanity: the real path wrote a polygon (ST_GeomFromGeoJSON ran on MySQL).
        assert status == "defined"
        await s.commit()
        return area.id, nbhd.id


async def _cleanup(factory: async_sessionmaker[AsyncSession], *, area_id: int) -> None:
    """Remove the seeded catalog row(s) + area so re-runs start clean."""
    async with factory() as s:
        await s.execute(
            text("DELETE FROM neighborhoods_catalog WHERE area_id = :area_id"),
            {"area_id": area_id},
        )
        await s.execute(text("DELETE FROM areas WHERE id = :id"), {"id": area_id})
        await s.commit()


@pytest.mark.asyncio
async def test_point_inside_polygon_is_eligible(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    """A point INSIDE the polygon is returned by point_in_polygon (ST_Contains)."""
    area_id, nbhd_id = await _seed_area_with_polygon(mysql_session)
    try:
        lat, lng = POINT_INSIDE
        async with mysql_session() as s:
            eligible = await point_in_polygon(s, area_id=area_id, lat=lat, lng=lng)
        assert nbhd_id in eligible
    finally:
        await _cleanup(mysql_session, area_id=area_id)


@pytest.mark.asyncio
async def test_point_outside_polygon_not_eligible(
    mysql_session: async_sessionmaker[AsyncSession],
) -> None:
    """A point OUTSIDE the polygon is NOT returned by point_in_polygon (MySQL)."""
    area_id, nbhd_id = await _seed_area_with_polygon(mysql_session)
    try:
        lat, lng = POINT_OUTSIDE
        async with mysql_session() as s:
            eligible = await point_in_polygon(s, area_id=area_id, lat=lat, lng=lng)
        assert nbhd_id not in eligible
        assert eligible == []
    finally:
        await _cleanup(mysql_session, area_id=area_id)
