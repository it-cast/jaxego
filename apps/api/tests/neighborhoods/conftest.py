"""Fixtures for the neighborhood-catalog tests (Phase 6).

The catalog-by-name tests run on the SQLite in-memory DB (Layer 2 of
tests/conftest.py). The spatial tests (ST_Contains) require MySQL 8 and are
marked `@pytest.mark.mysql` (skipped in dev, run in CI against real MySQL).

The polygon fixtures below are a small KNOWN square around a Pádua-ish lat/lng,
plus a point INSIDE and a point OUTSIDE that square. GeoJSON coordinates are
`[lng, lat]` (GeoJSON axis order); the inside/outside points are expressed as
(lat, lng) so the `ST_GeomFromText('POINT(lat lng)', 4326)` helper (lat-first —
Pitfall 2) can consume them directly.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# A small square around (lat ~ -21.81, lng ~ -42.18) — Pádua-ish. GeoJSON is a
# Polygon whose linear ring is CLOSED (first == last) with [lng, lat] pairs.
PADUA_LNG = -42.18
PADUA_LAT = -21.81
_HALF = 0.01  # ~1.1 km box edge half-width

PADUA_SQUARE_GEOJSON: dict = {
    "type": "Polygon",
    "coordinates": [
        [
            [PADUA_LNG - _HALF, PADUA_LAT - _HALF],
            [PADUA_LNG + _HALF, PADUA_LAT - _HALF],
            [PADUA_LNG + _HALF, PADUA_LAT + _HALF],
            [PADUA_LNG - _HALF, PADUA_LAT + _HALF],
            [PADUA_LNG - _HALF, PADUA_LAT - _HALF],
        ]
    ],
}

# (lat, lng) — lat first, to match the WKT SRID-4326 axis order helper.
POINT_INSIDE: tuple[float, float] = (PADUA_LAT, PADUA_LNG)
POINT_OUTSIDE: tuple[float, float] = (PADUA_LAT + 1.0, PADUA_LNG + 1.0)

# An invalid (self-intersecting "bowtie") polygon for the anti-DoS validation test.
BOWTIE_GEOJSON: dict = {
    "type": "Polygon",
    "coordinates": [
        [
            [0.0, 0.0],
            [1.0, 1.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 0.0],
        ]
    ],
}


@pytest_asyncio.fixture
async def neighborhood_seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, object]:
    """Seed two areas + an admin user; return the ids the catalog tests need."""
    async with session_factory() as s:
        area_a = Area(codename="padua", name="Pádua", config={})
        area_b = Area(codename="itaocara", name="Itaocara", config={})
        s.add_all([area_a, area_b])
        await s.flush()
        admin = User(
            email="admin.area@example.com",
            name="Admin Área",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add(admin)
        await s.commit()
        await s.refresh(area_a)
        await s.refresh(area_b)
        await s.refresh(admin)
        return {
            "area_a_id": area_a.id,
            "area_b_id": area_b.id,
            "admin_id": admin.id,
        }


@pytest.fixture
def padua_square() -> dict:
    """The known test polygon (GeoJSON Polygon)."""
    return PADUA_SQUARE_GEOJSON
