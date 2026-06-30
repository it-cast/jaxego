"""Neighborhood catalog service — area-scoped CRUD (D-01/D-02, REQ-003).

Every operation is AREA-SCOPED: the WHERE always carries `area_id = scope`, so a
neighborhood from another area returns 404 (not 403) — existence is not leaked
(A01). Polygon support was removed; neighborhoods are identified by name only.

Removal with active deliveries is blocked (archive instead).
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.neighborhoods.models import Neighborhood
from app.neighborhoods.schemas import NeighborhoodCreate

logger = structlog.get_logger("neighborhoods")


class NeighborhoodHasActiveDeliveriesError(AppError):
    """A neighborhood with active deliveries cannot be removed — archive it (409)."""

    status_code = 409
    code = "neighborhood_has_active_deliveries"

    def __init__(self, name: str) -> None:
        super().__init__(
            f'Não é possível remover "{name}": há entregas ativas nesse bairro. Arquive primeiro.'
        )


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
) -> Neighborhood:
    """Create a neighborhood by name."""
    now = datetime.now(UTC)
    nbhd = Neighborhood(
        area_id=area_id,
        name=body.name,
        is_informal=body.is_informal,
        created_at=now,
        updated_at=now,
    )
    session.add(nbhd)
    await session.flush()
    logger.info("neighborhood.create", area_id=area_id, nbhd_id=nbhd.id)
    return nbhd


async def list_neighborhoods(
    session: AsyncSession, *, area_id: int
) -> list[Neighborhood]:
    """List the area's non-archived neighborhoods ordered by name."""
    stmt = (
        select(Neighborhood)
        .where(Neighborhood.area_id == area_id, Neighborhood.archived_at.is_(None))
        .order_by(Neighborhood.name)
    )
    return list((await session.execute(stmt)).scalars().all())


async def archive_neighborhood(
    session: AsyncSession, *, area_id: int, nbhd_id: int
) -> Neighborhood:
    """Soft-archive a neighborhood (aware-UTC)."""
    nbhd = await _get_scoped(session, area_id=area_id, nbhd_id=nbhd_id)
    nbhd.archived_at = datetime.now(UTC)
    await session.flush()
    logger.info("neighborhood.archive", area_id=area_id, nbhd_id=nbhd_id)
    return nbhd


async def remove_neighborhood(session: AsyncSession, *, area_id: int, nbhd_id: int) -> None:
    """Hard-delete a neighborhood unless it has active deliveries (then 409)."""
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
