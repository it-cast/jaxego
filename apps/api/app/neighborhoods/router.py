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

from app.auth.dependencies import AreaScopeDep, CurrentUser, ForbiddenError, require_role
from app.db.session import get_session
from app.neighborhoods import service
from app.neighborhoods.schemas import NeighborhoodCreate, NeighborhoodRead, NeighborhoodUpdate

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AdminArea = Annotated[CurrentUser, Depends(require_role("admin_area"))]


def _read(nbhd) -> NeighborhoodRead:
    return NeighborhoodRead(
        id=nbhd.id,
        area_id=nbhd.area_id,
        name=nbhd.name,
        is_informal=nbhd.is_informal,
    )


def _require_scope(scope: int | None) -> int:
    if scope is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Bairro não encontrado.")
    return scope


@router.get("/catalog", response_model=list[NeighborhoodRead])
async def list_neighborhoods_catalog(
    user: CurrentUser,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[NeighborhoodRead]:
    """Read-only neighborhood list for any authenticated user scoped to an area."""
    if scope is None:
        raise ForbiddenError("Sem área definida para listagem de bairros.")
    rows = await service.list_neighborhoods(session, area_id=scope)
    return [_read(n) for n in rows]


@router.post("", response_model=NeighborhoodRead, status_code=status.HTTP_201_CREATED)
async def create_neighborhood(
    body: NeighborhoodCreate,
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> NeighborhoodRead:
    area_id = _require_scope(scope)
    nbhd = await service.create_neighborhood(session, area_id=area_id, body=body)
    await session.commit()
    return _read(nbhd)


@router.get("", response_model=list[NeighborhoodRead])
async def list_neighborhoods(
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[NeighborhoodRead]:
    area_id = _require_scope(scope)
    rows = await service.list_neighborhoods(session, area_id=area_id)
    return [_read(n) for n in rows]


@router.patch("/{nbhd_id}", response_model=NeighborhoodRead)
async def update_neighborhood(
    nbhd_id: int,
    body: NeighborhoodUpdate,
    _admin: AdminArea,
    scope: AreaScopeDep,
    session: SessionDep,
) -> NeighborhoodRead:
    area_id = _require_scope(scope)
    nbhd = await service.update_neighborhood(session, area_id=area_id, nbhd_id=nbhd_id, body=body)
    await session.commit()
    return _read(nbhd)


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
    return _read(nbhd)


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
