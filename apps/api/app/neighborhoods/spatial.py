"""Spatial helpers — the SINGLE owner of axis order + func.ST_* (Pitfall 2).

GeoJSON coordinates are `[lng, lat]`; MySQL WKT in SRID 4326 is LAT-FIRST. Mixing
the two silently breaks eligibility. To keep that confusion in one place:

- `validate_polygon_geojson` runs shapely server-side BEFORE the DB (anti-DoS):
  type == Polygon, ring closed / no self-intersection (`is_valid`), vertex cap,
  and lat∈[-90,90] / lng∈[-180,180].
- `GEOM_FROM_GEOJSON_SQL` / `point_from_latlng_sql` produce the parametrised SQL
  fragments (no f-string of a VALUE — A03). `ST_GeomFromGeoJSON` itself handles
  the GeoJSON→SRID-4326 axis reorder, so polygons are NOT pre-transformed.
- `point_in_polygon` builds the `ST_Contains(polygon, POINT(lat lng))` query
  (lat first) used for eligibility (consumed by Phase 8).

All spatial functions require live MySQL 8 — SQLite has none. Polygon VALIDATION
(shapely) is pure Python and runs everywhere; only the DB round-trips are
`@pytest.mark.mysql`.
"""

from __future__ import annotations

from sqlalchemy import bindparam, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.neighborhoods.models import Neighborhood

# Cap on total polygon vertices (anti-DoS — A4 of the RESEARCH; urban
# neighborhood is well under this).
MAX_POLYGON_VERTICES = 2000


class InvalidPolygonError(AppError):
    """The submitted GeoJSON is not an acceptable Polygon (422)."""

    status_code = 422
    code = "invalid_polygon"


def validate_polygon_geojson(gj: dict, *, max_vertices: int = MAX_POLYGON_VERTICES) -> None:
    """Validate a GeoJSON Polygon server-side BEFORE touching the DB.

    Raises `InvalidPolygonError` (422) with an actionable pt-BR message. shapely
    catches structural problems (open ring, self-intersection); we add the vertex
    cap and the coordinate-range check.
    """
    # Imported lazily so modules that never validate a polygon don't pull shapely.
    from shapely.geometry import Polygon, shape

    if not isinstance(gj, dict) or gj.get("type") != "Polygon":
        raise InvalidPolygonError("GeoJSON inválido. Cole um Polygon com pares lng,lat.")

    try:
        geom = shape(gj)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise InvalidPolygonError("GeoJSON inválido. Cole um Polygon com pares lng,lat.") from exc

    if not isinstance(geom, Polygon):
        raise InvalidPolygonError("GeoJSON inválido. Cole um Polygon com pares lng,lat.")

    if geom.is_empty or not geom.is_valid:
        raise InvalidPolygonError("Polígono inválido (anel aberto ou auto-interseção?).")

    rings = [geom.exterior, *geom.interiors]
    n = sum(len(ring.coords) for ring in rings)
    if n > max_vertices:
        raise InvalidPolygonError(f"Polígono com vértices demais ({n} > {max_vertices}).")

    # Coordinate range check (lng,lat in GeoJSON order).
    for ring in rings:
        for lng, lat in ring.coords:
            if not (-180.0 <= lng <= 180.0):
                raise InvalidPolygonError("Coordenada fora de faixa. Use lng entre −180 e 180.")
            if not (-90.0 <= lat <= 90.0):
                raise InvalidPolygonError("Coordenada fora de faixa. Use lat entre −90 e 90.")


# Parametrised SQL fragment that turns a GeoJSON string into a SRID-4326 geometry.
# options=2 → accept only geometry objects. The GeoJSON axis reorder is automatic.
GEOM_FROM_GEOJSON_SQL = "ST_GeomFromGeoJSON(:gj, 2, 4326)"


def point_from_latlng_sql() -> str:
    """SQL fragment for a SRID-4326 POINT built from lat/lng binds (lat FIRST)."""
    # WKT in SRID 4326 is lat-first (Pitfall 2). Binds are parametrised (A03);
    # CONCAT keeps the value out of the SQL string.
    return "ST_GeomFromText(CONCAT('POINT(', :lat, ' ', :lng, ')'), 4326)"


async def point_in_polygon(
    session: AsyncSession, *, lat: float, lng: float, area_id: int
) -> list[int]:
    """Return the ids of the area's neighborhoods whose polygon CONTAINS the point.

    Uses `ST_Contains(polygon, POINT(lat lng))` with lat-first axis order. Only
    neighborhoods that actually have a polygon participate (NULL polygons never
    match). Requires live MySQL 8 — this is the eligibility primitive Phase 8 uses.
    """
    stmt = (
        select(Neighborhood.id)
        .where(
            Neighborhood.area_id == area_id,
            Neighborhood.archived_at.is_(None),
            func.ST_Contains(
                text("polygon"),
                text(point_from_latlng_sql()),
            ),
        )
        .params(lat=lat, lng=lng)
    )
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]


async def polygon_as_geojson(session: AsyncSession, *, area_id: int, nbhd_id: int) -> dict | None:
    """Read a neighborhood's polygon back as GeoJSON (None if no polygon/no row)."""
    import json

    stmt = text(
        "SELECT ST_AsGeoJSON(polygon) AS gj FROM neighborhoods_catalog "
        "WHERE id = :id AND area_id = :area_id"
    ).bindparams(bindparam("id", nbhd_id), bindparam("area_id", area_id))
    row = (await session.execute(stmt)).mappings().one_or_none()
    if row is None or row["gj"] is None:
        return None
    return json.loads(row["gj"])
