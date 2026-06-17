"""/v1/admin/area — area-admin self-service (read + config patch).

Area admins can read and update ONLY their own area (scoped via the token's
area_scope — D-06). No cross-area access is possible here. Config changes are
audited (RN-012 / F-08 E2) without the cross_area_bypass flag.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas import service
from app.areas.schemas import AreaRead, AreaUpdate
from app.audit.service import write_audit
from app.auth.dependencies import AreaScopeDep, require_role
from app.auth.models import User
from app.db.session import get_session

router = APIRouter(prefix="/admin/area", tags=["admin-area"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AreaAdminDep = Annotated[User, Depends(require_role("admin_area"))]


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
