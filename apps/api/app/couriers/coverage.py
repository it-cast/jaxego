"""Courier coverage (RN-003 / REQ-016) — include/exclude over the catalog.

A courier declares the neighborhoods they serve (include) and the ones they
refuse (exclude). Eligibility (consumed by the Phase 8 dispatch) requires coverage
at BOTH points — pickup AND dropoff — and an exclusion vetoes BOTH. `is_eligible`
is a PURE function over the coverage rows (Pattern 3 of the RESEARCH), testable in
SQLite.

`set_coverage` replaces the courier's rows (delete + insert, area-scoped, one
query each — no N+1). Every neighborhood must belong to the same area (else 404/
422 — no cross-area reference). A neighborhood may not be both included and
excluded.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.couriers.models import CourierCoverageArea
from app.neighborhoods.models import Neighborhood

logger = structlog.get_logger("couriers.coverage")


class InvalidCoverageError(AppError):
    """Coverage references a neighborhood outside the area or both include+exclude."""

    status_code = 422
    code = "invalid_coverage"


def is_eligible(coverage: Iterable, pickup_nbhd_id: int, dropoff_nbhd_id: int) -> bool:
    """Eligible iff BOTH points are included and NEITHER is excluded (RN-003).

    `coverage` is any iterable of rows exposing `.neighborhood_id` and `.kind`
    ('include' | 'exclude'). An exclusion vetoes both points.
    """
    included: set[int] = set()
    excluded: set[int] = set()
    for row in coverage:
        if row.kind == "include":
            included.add(row.neighborhood_id)
        elif row.kind == "exclude":
            excluded.add(row.neighborhood_id)
    points = {pickup_nbhd_id, dropoff_nbhd_id}
    if points & excluded:
        return False
    return points <= included


async def _validate_in_area(
    session: AsyncSession, *, area_id: int, neighborhood_ids: set[int]
) -> None:
    """Reject any neighborhood id that is not in this area (no cross-area leak)."""
    if not neighborhood_ids:
        return
    stmt = select(Neighborhood.id).where(
        Neighborhood.area_id == area_id, Neighborhood.id.in_(neighborhood_ids)
    )
    found = {row[0] for row in (await session.execute(stmt)).all()}
    missing = neighborhood_ids - found
    if missing:
        raise InvalidCoverageError("Bairro de cobertura não pertence à área.")


async def set_coverage(
    session: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
    includes: Sequence[int],
    excludes: Sequence[int],
) -> None:
    """Replace the courier's coverage rows (delete + insert, area-scoped)."""
    inc = set(includes)
    exc = set(excludes)
    overlap = inc & exc
    if overlap:
        raise InvalidCoverageError("Um bairro não pode estar incluído e excluído ao mesmo tempo.")
    await _validate_in_area(session, area_id=area_id, neighborhood_ids=inc | exc)

    await session.execute(
        delete(CourierCoverageArea).where(
            CourierCoverageArea.area_id == area_id,
            CourierCoverageArea.courier_id == courier_id,
        )
    )
    now = datetime.now(UTC)  # AWARE — TD-010
    rows = [
        CourierCoverageArea(
            area_id=area_id,
            courier_id=courier_id,
            neighborhood_id=nid,
            kind=kind,
            created_at=now,
            updated_at=now,
        )
        for nid, kind in (
            *((n, "include") for n in inc),
            *((n, "exclude") for n in exc),
        )
    ]
    session.add_all(rows)
    await session.flush()
    logger.info(
        "courier.coverage.update",
        area_id=area_id,
        courier_id=courier_id,
        includes=len(inc),
        excludes=len(exc),
    )


async def list_coverage(
    session: AsyncSession, *, area_id: int, courier_id: int
) -> list[CourierCoverageArea]:
    """List the courier's coverage rows (single query, no N+1)."""
    stmt = select(CourierCoverageArea).where(
        CourierCoverageArea.area_id == area_id,
        CourierCoverageArea.courier_id == courier_id,
    )
    return list((await session.execute(stmt)).scalars().all())
