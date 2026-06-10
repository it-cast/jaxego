"""Neighborhood catalog service — area-scoped CRUD (D-01/D-02, REQ-003).

Every operation is AREA-SCOPED: the WHERE always carries `area_id = scope`, so a
neighborhood from another area returns 404 (not 403) — existence is not leaked
(A01 / item 2 of the Security Notes). A neighborhood is valid by NAME alone; the
polygon is OPTIONAL and, when present, is validated (shapely) and persisted via
`ST_GeomFromGeoJSON` (SQL Core — the column is out of the ORM, LOW-1).

Removal with active deliveries is blocked (archive instead). The "active
deliveries" table arrives in Phase 7; until then the guard is structural (any
coverage/pricing reference to the neighborhood blocks the hard delete) and the
SUGGESTION to complete the check against `deliveries` is recorded.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.neighborhoods.models import Neighborhood
from app.neighborhoods.schemas import NeighborhoodCreate
from app.neighborhoods.spatial import validate_polygon_geojson

logger = structlog.get_logger("neighborhoods")


class NeighborhoodHasActiveDeliveriesError(AppError):
    """A neighborhood with active deliveries cannot be removed — archive it (409)."""

    status_code = 409
    code = "neighborhood_has_active_deliveries"

    def __init__(self, name: str) -> None:
        super().__init__(
            f'Não é possível remover "{name}": há entregas ativas nesse bairro. Arquive primeiro.'
        )


def _polygon_status(has_polygon: bool) -> str:
    return "defined" if has_polygon else "by_name"


async def _get_scoped(session: AsyncSession, *, area_id: int | None, nbhd_id: int) -> Neighborhood:
    """Load a neighborhood within the area scope or raise 404 (no existence leak)."""
    stmt = select(Neighborhood).where(Neighborhood.id == nbhd_id)
    if area_id is not None:
        stmt = stmt.where(Neighborhood.area_id == area_id)
    nbhd = (await session.execute(stmt)).scalar_one_or_none()
    if nbhd is None or nbhd.archived_at is not None:
        raise NotFoundError("Bairro não encontrado.")
    return nbhd


async def create_neighborhood(
    session: AsyncSession, *, area_id: int, body: NeighborhoodCreate
) -> tuple[Neighborhood, str]:
    """Create a neighborhood (with or without polygon). Returns (row, polygon_status).

    A polygon, if given, is validated server-side (shapely — anti-DoS) and written
    via `ST_GeomFromGeoJSON` (Pattern 1). Name-only inserts leave polygon NULL.
    """
    has_polygon = body.polygon_geojson is not None
    if has_polygon:
        validate_polygon_geojson(body.polygon_geojson)  # type: ignore[arg-type]

    now = datetime.now(UTC)  # AWARE — TD-010
    nbhd = Neighborhood(
        area_id=area_id,
        name=body.name,
        is_informal=body.is_informal,
        created_at=now,
        updated_at=now,
    )
    session.add(nbhd)
    await session.flush()

    if has_polygon and session.bind is not None and session.bind.dialect.name == "mysql":
        # MySQL-only: set the spatial column via ST_GeomFromGeoJSON (binds — A03).
        await session.execute(
            text(
                "UPDATE neighborhoods_catalog SET polygon = ST_GeomFromGeoJSON(:gj, 2, 4326) "
                "WHERE id = :id AND area_id = :area_id"
            ),
            {"gj": json.dumps(body.polygon_geojson), "id": nbhd.id, "area_id": area_id},
        )

    logger.info(
        "neighborhood.create",
        area_id=area_id,
        nbhd_id=nbhd.id,
        has_polygon=has_polygon,
    )
    # On MySQL the polygon is now defined; on SQLite there is no polygon column.
    is_mysql = session.bind is not None and session.bind.dialect.name == "mysql"
    return nbhd, _polygon_status(has_polygon and is_mysql)


async def list_neighborhoods(
    session: AsyncSession, *, area_id: int
) -> list[tuple[Neighborhood, str]]:
    """List the area's non-archived neighborhoods (single query, no N+1).

    Polygon status is derived: on MySQL via `polygon IS NOT NULL`; on SQLite the
    column does not exist, so everything reports 'by_name'.
    """
    is_mysql = session.bind is not None and session.bind.dialect.name == "mysql"

    if is_mysql:
        stmt = (
            select(Neighborhood, func.if_(text("polygon IS NOT NULL"), 1, 0).label("has_poly"))
            .where(Neighborhood.area_id == area_id, Neighborhood.archived_at.is_(None))
            .order_by(Neighborhood.name)
        )
        rows = (await session.execute(stmt)).all()
        return [(r[0], _polygon_status(bool(r[1]))) for r in rows]

    stmt2 = (
        select(Neighborhood)
        .where(Neighborhood.area_id == area_id, Neighborhood.archived_at.is_(None))
        .order_by(Neighborhood.name)
    )
    nbhds = list((await session.execute(stmt2)).scalars().all())
    return [(n, "by_name") for n in nbhds]


async def update_polygon(
    session: AsyncSession, *, area_id: int, nbhd_id: int, polygon_geojson: dict
) -> Neighborhood:
    """Validate + set/replace a neighborhood's polygon (MySQL ST_GeomFromGeoJSON)."""
    nbhd = await _get_scoped(session, area_id=area_id, nbhd_id=nbhd_id)
    validate_polygon_geojson(polygon_geojson)
    if session.bind is not None and session.bind.dialect.name == "mysql":
        await session.execute(
            text(
                "UPDATE neighborhoods_catalog SET polygon = ST_GeomFromGeoJSON(:gj, 2, 4326), "
                "updated_at = :now WHERE id = :id AND area_id = :area_id"
            ),
            {
                "gj": json.dumps(polygon_geojson),
                "now": datetime.now(UTC),
                "id": nbhd_id,
                "area_id": area_id,
            },
        )
    logger.info("neighborhood.update_polygon", area_id=area_id, nbhd_id=nbhd_id)
    return nbhd


async def archive_neighborhood(
    session: AsyncSession, *, area_id: int, nbhd_id: int
) -> Neighborhood:
    """Soft-archive a neighborhood (aware-UTC, TD-010)."""
    nbhd = await _get_scoped(session, area_id=area_id, nbhd_id=nbhd_id)
    nbhd.archived_at = datetime.now(UTC)
    await session.flush()
    logger.info("neighborhood.archive", area_id=area_id, nbhd_id=nbhd_id)
    return nbhd


async def remove_neighborhood(session: AsyncSession, *, area_id: int, nbhd_id: int) -> None:
    """Hard-delete a neighborhood unless it has active deliveries (then 409).

    The deliveries table arrives in Phase 7; for M1 the guard blocks deletion when
    the neighborhood is still referenced by any coverage/pricing row (a proxy for
    "in use"). The full "active deliveries" check is completed in Phase 7.
    """
    nbhd = await _get_scoped(session, area_id=area_id, nbhd_id=nbhd_id)

    referenced = (
        await session.execute(
            text(
                "SELECT 1 FROM courier_coverage_areas WHERE neighborhood_id = :id "
                "UNION SELECT 1 FROM courier_pricing_tables WHERE neighborhood_id = :id "
                "LIMIT 1"
            ),
            {"id": nbhd_id},
        )
    ).first()
    if referenced is not None:
        raise NeighborhoodHasActiveDeliveriesError(nbhd.name)

    await session.delete(nbhd)
    await session.flush()
    logger.info("neighborhood.remove", area_id=area_id, nbhd_id=nbhd_id)
