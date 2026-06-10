"""/v1/neighborhoods — area admin curates the per-area catalog (D-02, REQ-003).

Every route is gated by `require_role("admin_area")` + `area_scope`: the area is
resolved by the dependency and pushed into the service WHERE clause, so a
neighborhood from another area returns 404 (not 403 — no existence leak, item 2
of the Security Notes). `commit()` happens in the router (the phase pattern).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.db.session import get_session
from app.neighborhoods import service
from app.neighborhoods.schemas import (
    NeighborhoodCreate,
    NeighborhoodPolygonUpdate,
    NeighborhoodRead,
)

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AdminArea = Annotated[CurrentUser, Depends(require_role("admin_area"))]


def _read(nbhd, polygon_status: str) -> NeighborhoodRead:
    return NeighborhoodRead(
        id=nbhd.id,
        area_id=nbhd.area_id,
        name=nbhd.name,
        is_informal=nbhd.is_informal,
        polygon_status=polygon_status,  # type: ignore[arg-type]
    )


def _require_scope(scope: int | None) -> int:
    """An area admin always has a concrete scope; reject a None (platform) scope."""
    if scope is None:
        # A platform admin has no single area; the catalog is curated per-area.
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Bairro não encontrado.")
    return scope


@router.post("", response_model=NeighborhoodRead, status_code=status.HTTP_201_CREATED)
async def create_neighborhood(
    body: NeighborhoodCreate,
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> NeighborhoodRead:
    area_id = _require_scope(scope)
    nbhd, polygon_status = await service.create_neighborhood(session, area_id=area_id, body=body)
    await session.commit()
    return _read(nbhd, polygon_status)


@router.get("", response_model=list[NeighborhoodRead])
async def list_neighborhoods(
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[NeighborhoodRead]:
    area_id = _require_scope(scope)
    rows = await service.list_neighborhoods(session, area_id=area_id)
    return [_read(n, status_) for n, status_ in rows]


@router.patch("/{nbhd_id}/polygon", response_model=NeighborhoodRead)
async def update_polygon(
    nbhd_id: int,
    body: NeighborhoodPolygonUpdate,
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> NeighborhoodRead:
    area_id = _require_scope(scope)
    nbhd = await service.update_polygon(
        session, area_id=area_id, nbhd_id=nbhd_id, polygon_geojson=body.polygon_geojson
    )
    await session.commit()
    return _read(nbhd, "defined")


@router.post("/{nbhd_id}/archive", response_model=NeighborhoodRead)
async def archive_neighborhood(
    nbhd_id: int,
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> NeighborhoodRead:
    area_id = _require_scope(scope)
    nbhd = await service.archive_neighborhood(session, area_id=area_id, nbhd_id=nbhd_id)
    await session.commit()
    return _read(nbhd, "by_name")


@router.delete("/{nbhd_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_neighborhood(
    nbhd_id: int,
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> None:
    area_id = _require_scope(scope)
    await service.remove_neighborhood(session, area_id=area_id, nbhd_id=nbhd_id)
    await session.commit()
