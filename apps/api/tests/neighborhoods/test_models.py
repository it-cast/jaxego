"""Neighborhood catalog by NAME (REQ-003) — SQLite, no live MySQL.

A neighborhood is valid with just a NAME (polygon optional in M1). It is
AREA-SCOPED: the same name may exist in two areas, but the catalog read is
filtered by `area_id`. Polygon persistence/reads use MySQL spatial functions and
are covered by `test_spatial.py` (@pytest.mark.mysql).

These import `app.neighborhoods.models` lazily via `pytest.importorskip` so the
Wave 0 scaffold COLLECTS without ImportError before Plan 02 creates the module.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_neighborhood_name_only_persists(db_session, neighborhood_seed) -> None:
    """REQ-003: a neighborhood with only a name persists and reads (area-scoped)."""
    models = pytest.importorskip("app.neighborhoods.models")

    nbhd = models.Neighborhood(
        area_id=neighborhood_seed["area_a_id"],
        name="Centro",
    )
    db_session.add(nbhd)
    await db_session.flush()

    assert nbhd.id is not None
    assert nbhd.name == "Centro"
    assert nbhd.area_id == neighborhood_seed["area_a_id"]
    assert nbhd.is_informal is False
    assert nbhd.archived_at is None


@pytest.mark.asyncio
async def test_same_name_two_areas_allowed(db_session, neighborhood_seed) -> None:
    """A name may repeat across areas (catalog is per-area, area-scoped)."""
    models = pytest.importorskip("app.neighborhoods.models")

    a = models.Neighborhood(area_id=neighborhood_seed["area_a_id"], name="Centro")
    b = models.Neighborhood(area_id=neighborhood_seed["area_b_id"], name="Centro")
    db_session.add_all([a, b])
    await db_session.flush()

    assert a.id != b.id
    assert a.name == b.name
    assert a.area_id != b.area_id


@pytest.mark.asyncio
async def test_informal_flag(db_session, neighborhood_seed) -> None:
    """D-01: informal neighborhoods are supported via is_informal=True."""
    models = pytest.importorskip("app.neighborhoods.models")

    nbhd = models.Neighborhood(
        area_id=neighborhood_seed["area_a_id"],
        name="Vila do Pescador",
        is_informal=True,
    )
    db_session.add(nbhd)
    await db_session.flush()
    assert nbhd.is_informal is True
