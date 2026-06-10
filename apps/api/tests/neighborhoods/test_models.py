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


# --- service CRUD area-scoped (REQ-003) ---
@pytest.mark.asyncio
async def test_create_and_list_name_only(db_session, neighborhood_seed) -> None:
    """create_neighborhood (name only) then list returns it as 'by_name'."""
    service = pytest.importorskip("app.neighborhoods.service")
    from app.neighborhoods.schemas import NeighborhoodCreate

    area_a = neighborhood_seed["area_a_id"]
    nbhd, status = await service.create_neighborhood(
        db_session, area_id=area_a, body=NeighborhoodCreate(name="Centro")
    )
    assert status == "by_name"
    rows = await service.list_neighborhoods(db_session, area_id=area_a)
    assert [r[0].name for r in rows] == ["Centro"]
    assert nbhd.id == rows[0][0].id


@pytest.mark.asyncio
async def test_cross_area_get_is_404(db_session, neighborhood_seed) -> None:
    """A neighborhood from area A is invisible to area B's scope → 404."""
    service = pytest.importorskip("app.neighborhoods.service")
    from app.core.exceptions import NotFoundError
    from app.neighborhoods.schemas import NeighborhoodCreate

    nbhd, _ = await service.create_neighborhood(
        db_session,
        area_id=neighborhood_seed["area_a_id"],
        body=NeighborhoodCreate(name="Centro"),
    )
    with pytest.raises(NotFoundError):
        await service.archive_neighborhood(
            db_session,
            area_id=neighborhood_seed["area_b_id"],  # wrong scope
            nbhd_id=nbhd.id,
        )


@pytest.mark.asyncio
async def test_archived_not_listed(db_session, neighborhood_seed) -> None:
    """An archived neighborhood drops out of the listing."""
    service = pytest.importorskip("app.neighborhoods.service")
    from app.neighborhoods.schemas import NeighborhoodCreate

    area_a = neighborhood_seed["area_a_id"]
    nbhd, _ = await service.create_neighborhood(
        db_session, area_id=area_a, body=NeighborhoodCreate(name="Aldeia")
    )
    await service.archive_neighborhood(db_session, area_id=area_a, nbhd_id=nbhd.id)
    rows = await service.list_neighborhoods(db_session, area_id=area_a)
    assert rows == []


@pytest.mark.asyncio
async def test_invalid_polygon_rejected(db_session, neighborhood_seed) -> None:
    """A self-intersecting polygon is rejected at create (422) — anti-DoS."""
    service = pytest.importorskip("app.neighborhoods.service")
    from app.neighborhoods.schemas import NeighborhoodCreate
    from app.neighborhoods.spatial import InvalidPolygonError

    from tests.neighborhoods.conftest import BOWTIE_GEOJSON

    with pytest.raises(InvalidPolygonError):
        await service.create_neighborhood(
            db_session,
            area_id=neighborhood_seed["area_a_id"],
            body=NeighborhoodCreate(name="Bairro Ruim", polygon_geojson=BOWTIE_GEOJSON),
        )
