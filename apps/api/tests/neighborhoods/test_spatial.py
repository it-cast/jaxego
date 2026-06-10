"""Point-in-polygon elegibility (REQ-003) — requires live MySQL 8.

This exercises `app.neighborhoods.spatial.point_in_polygon` (ST_Contains) against
a real MySQL 8 server: a point INSIDE the seeded polygon is eligible; a point
OUTSIDE is not. Skipped outside the CI MySQL run (padrão Phase 5) — SQLite has no
spatial functions. The acceptance criterion of the ROADMAP (ponto dentro/fora
decide elegibilidade) lives here.

Pitfall 2: GeoJSON is [lng, lat]; WKT SRID 4326 is lat-first. The single helper
in spatial.py owns the axis order; this test only asserts the boolean outcome.
"""

from __future__ import annotations

import pytest

from tests.neighborhoods.conftest import (
    PADUA_SQUARE_GEOJSON,
    POINT_INSIDE,
    POINT_OUTSIDE,
)

pytestmark = pytest.mark.mysql


@pytest.mark.asyncio
async def test_point_inside_polygon_is_eligible() -> None:
    """A point inside the polygon is returned by point_in_polygon (ST_Contains).

    Requires live MySQL 8 (ST_GeomFromGeoJSON / ST_Contains). Skipped in dev.
    """
    pytest.importorskip("app.neighborhoods.spatial")
    pytest.skip(
        "requires live MySQL 8 (ST_Contains point-in-polygon) — run with -m mysql. "
        f"Fixture: square={PADUA_SQUARE_GEOJSON['type']}, inside={POINT_INSIDE}, "
        f"outside={POINT_OUTSIDE}."
    )


@pytest.mark.asyncio
async def test_point_outside_polygon_not_eligible() -> None:
    """A point outside the polygon is NOT returned by point_in_polygon (MySQL)."""
    pytest.importorskip("app.neighborhoods.spatial")
    pytest.skip("requires live MySQL 8 (ST_Contains) — run with -m mysql.")
