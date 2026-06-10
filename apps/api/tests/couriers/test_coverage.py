"""Courier coverage (RN-003 / REQ-016) — SQLite, no live MySQL.

Eligibility requires coverage at BOTH points (pickup AND dropoff); an exclusion
vetoes both. `is_eligible` is a PURE function over the coverage rows (Pattern 3 of
the RESEARCH) — it is the base the Phase 8 dispatch consumes.

Imports `app.couriers.coverage` lazily via `pytest.importorskip` so the Wave 0
scaffold COLLECTS before Plan 03 creates the module.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass
class _Row:
    """Minimal coverage row stand-in for the pure is_eligible test."""

    neighborhood_id: int
    kind: str  # 'include' | 'exclude'


def test_both_points_included_is_eligible() -> None:
    """RN-003: pickup AND dropoff both included → eligible."""
    coverage = pytest.importorskip("app.couriers.coverage")
    rows = [_Row(1, "include"), _Row(2, "include")]
    assert coverage.is_eligible(rows, pickup_nbhd_id=1, dropoff_nbhd_id=2) is True


def test_one_point_missing_not_eligible() -> None:
    """RN-003: if only one point is included, NOT eligible."""
    coverage = pytest.importorskip("app.couriers.coverage")
    rows = [_Row(1, "include")]
    assert coverage.is_eligible(rows, pickup_nbhd_id=1, dropoff_nbhd_id=2) is False


def test_excluded_point_vetoes_both() -> None:
    """RN-003: an excluded neighborhood vetoes eligibility at both points."""
    coverage = pytest.importorskip("app.couriers.coverage")
    rows = [_Row(1, "include"), _Row(2, "include"), _Row(2, "exclude")]
    assert coverage.is_eligible(rows, pickup_nbhd_id=1, dropoff_nbhd_id=2) is False
    # And exclusion at the pickup also vetoes.
    rows2 = [_Row(1, "include"), _Row(2, "include"), _Row(1, "exclude")]
    assert coverage.is_eligible(rows2, pickup_nbhd_id=1, dropoff_nbhd_id=2) is False


@pytest.mark.asyncio
async def test_set_coverage_area_scoped(db_session, courier_seed) -> None:
    """set_coverage persists include/exclude rows for a courier, area-scoped."""
    coverage = pytest.importorskip("app.couriers.coverage")
    models = pytest.importorskip("app.neighborhoods.models")
    from tests.couriers.conftest import make_courier

    courier = await make_courier(
        db_session,
        area_id=courier_seed["area_a_id"],
        user_id=courier_seed["user_id"],
        status="active",
    )
    n1 = models.Neighborhood(area_id=courier.area_id, name="Centro")
    n2 = models.Neighborhood(area_id=courier.area_id, name="Aldeia")
    db_session.add_all([n1, n2])
    await db_session.flush()

    await coverage.set_coverage(
        db_session,
        area_id=courier.area_id,
        courier_id=courier.id,
        includes=[n1.id, n2.id],
        excludes=[],
    )
    rows = await coverage.list_coverage(
        db_session, area_id=courier.area_id, courier_id=courier.id
    )
    included = {r.neighborhood_id for r in rows if r.kind == "include"}
    assert included == {n1.id, n2.id}
