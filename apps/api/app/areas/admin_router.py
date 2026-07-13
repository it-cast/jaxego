"""/v1/admin/area — area-admin self-service (read + config patch).

Area admins can read and update ONLY their own area (scoped via the token's
area_scope — D-06). No cross-area access is possible here. Config changes are
audited (RN-012 / F-08 E2) without the cross_area_bypass flag.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.areas import service
from app.areas.schemas import AreaRead, AreaUpdate, ZonaCreate, ZonaRead, ZonaUpdate
from app.audit.service import write_audit
from app.auth.dependencies import AreaScopeDep, require_role
from app.auth.principals import Actor
from app.db.session import get_session

router = APIRouter(prefix="/admin/area", tags=["admin-area"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AreaAdminDep = Annotated[Actor, Depends(require_role("admin_area"))]


@router.get("", response_model=AreaRead)
async def get_my_area(
    user: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> AreaRead:
    """Return the area that the authenticated admin belongs to."""
    assert scope is not None  # require_role('admin_area') guarantees a scope
    area = await service.get_area(session, scope)
    return AreaRead.model_validate(area)


@router.get("/zonas", response_model=list[ZonaRead])
async def list_zonas(
    user: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> list[ZonaRead]:
    """List all zones in the admin's area."""
    assert scope is not None
    zonas = await service.list_zonas(session, scope)
    return [ZonaRead.model_validate(z) for z in zonas]


@router.post("/zonas", response_model=ZonaRead, status_code=201)
async def create_zona(
    body: ZonaCreate,
    user: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> ZonaRead:
    """Create a new zone in the admin's area."""
    assert scope is not None
    zona = await service.create_zona(session, scope, body)
    await session.commit()
    return ZonaRead.model_validate(zona)


@router.patch("/zonas/{zona_id}", response_model=ZonaRead)
async def update_zona(
    zona_id: int,
    body: ZonaUpdate,
    user: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> ZonaRead:
    """Update a zone's name or boundary."""
    assert scope is not None
    zona = await service.update_zona(session, zona_id, scope, body)
    await session.commit()
    return ZonaRead.model_validate(zona)


@router.delete("/zonas/{zona_id}", status_code=204, response_class=Response)
async def delete_zona(
    zona_id: int,
    user: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> Response:
    """Delete a zone."""
    assert scope is not None
    await service.delete_zona(session, zona_id, scope)
    await session.commit()
    return Response(status_code=204)


@router.patch("/config", response_model=AreaRead)
async def patch_my_area_config(
    body: AreaUpdate,
    user: AreaAdminDep,
    scope: AreaScopeDep,
    request: Request,
    session: SessionDep,
) -> AreaRead:
    """Patch the config of the admin's own area; sensitive changes are audited."""
    assert scope is not None
    area, config_diff = await service.update_area(session, scope, body)
    if config_diff is not None:
        diff_before, diff_after = config_diff
        await write_audit(
            session,
            actor_id=user.id,
            action="area.config.update",
            area_id=scope,
            before=diff_before,
            after=diff_after,
            ip=request.client.host if request.client else None,
        )
    await session.commit()
    return AreaRead.model_validate(area)
