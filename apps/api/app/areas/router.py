"""/v1/areas endpoints — CRUD restricted to the platform admin (thin router).

Every route is gated by `require_platform_admin` (A01: separate dependency, no
`if user.is_admin` in the body — zero orphan routes). Because a platform admin
operates cross-area, EACH area access is recorded in `audit_log` with
`cross_area_bypass=True` (RN-001: the bypass is never silent). A non-existent or
archived area returns 404 (does not leak existence).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas import service
from app.areas.schemas import (
    AreaAdminAssignBody,
    AreaAdminRead,
    AreaCreate,
    AreaRead,
    AreaUpdate,
)
from app.audit.service import write_audit
from app.auth.dependencies import PlatformAdmin
from app.auth.principals import Actor
from app.db.session import get_session

router = APIRouter(prefix="/areas", tags=["areas"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _public_kyc_level(config: dict | None) -> str:
    """Public signup only exposes supported KYC levels; legacy values fall back safely."""
    raw = (config or {}).get("kyc_level", "simples")
    return raw if raw in {"simples", "completa"} else "simples"


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def _audit_bypass(
    session: AsyncSession,
    *,
    actor: Actor,
    action: str,
    area_id: int | None,
    request: Request,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    """Record a platform-admin cross-area access (RN-001, never silent)."""
    await write_audit(
        session,
        actor_id=actor.id,
        action=action,
        area_id=area_id,
        before=before,
        after=after,
        ip=_client_ip(request),
        cross_area_bypass=True,
    )


@router.post(
    "/{area_id}/admins",
    response_model=AreaAdminRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_area_admin(
    area_id: int,
    body: AreaAdminAssignBody,
    admin: PlatformAdmin,
    request: Request,
    session: SessionDep,
) -> AreaAdminRead:
    """Designar admin de área por e-mail (F3.3). Cria o vínculo ou atualiza o papel."""
    membership, email = await service.assign_area_admin(
        session, area_id=area_id, user_email=str(body.user_email), role=body.role
    )
    await _audit_bypass(
        session,
        actor=admin,
        action="area.admin_assigned",
        area_id=area_id,
        request=request,
        after={"user_id": membership.id, "role": membership.role},
    )
    await session.commit()
    return AreaAdminRead(
        id=membership.id,
        area_id=membership.area_id,
        user_id=membership.id,
        user_email=email,
        user_name=membership.name,
        role=membership.role,
    )


@router.post("", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
async def create_area(
    body: AreaCreate,
    admin: PlatformAdmin,
    request: Request,
    session: SessionDep,
) -> AreaRead:
    area = await service.create_area(session, body)
    await _audit_bypass(
        session,
        actor=admin,
        action="area.create",
        area_id=area.id,
        request=request,
        after={"codename": area.codename, "name": area.name},
    )
    await session.commit()
    return AreaRead.model_validate(area)


@router.get("/public", response_model=list[dict])
async def list_areas_public(session: SessionDep) -> list[dict]:
    """Public list of active areas for the courier signup (F-02 step 2). No auth."""
    areas = await service.list_areas(session)
    return [
        {
            "id": a.id,
            "name": a.name,
            "kyc_level": _public_kyc_level(a.config),
        }
        for a in areas
        if a.deleted_at is None
    ]


@router.get("", response_model=list[AreaRead])
async def list_areas(
    admin: PlatformAdmin,
    request: Request,
    session: SessionDep,
) -> list[AreaRead]:
    areas = await service.list_areas(session)
    await _audit_bypass(session, actor=admin, action="area.list", area_id=None, request=request)
    await session.commit()
    return [AreaRead.model_validate(a) for a in areas]


@router.get("/{area_id}", response_model=AreaRead)
async def get_area(
    area_id: int,
    admin: PlatformAdmin,
    request: Request,
    session: SessionDep,
) -> AreaRead:
    area = await service.get_area(session, area_id)
    await _audit_bypass(session, actor=admin, action="area.read", area_id=area_id, request=request)
    await session.commit()
    return AreaRead.model_validate(area)


@router.patch("/{area_id}", response_model=AreaRead)
async def update_area(
    area_id: int,
    body: AreaUpdate,
    admin: PlatformAdmin,
    request: Request,
    session: SessionDep,
) -> AreaRead:
    before = await service.get_area(session, area_id)
    before_snap = {"name": before.name, "config": before.config}
    area, config_diff = await service.update_area(session, area_id, body)
    await _audit_bypass(
        session,
        actor=admin,
        action="area.update",
        area_id=area_id,
        request=request,
        before=before_snap,
        after={"name": area.name, "config": area.config},
    )
    # Sensitive config change (piso/geofence/kyc_level/timeouts/retorno) → its own
    # before/after audit row (RN-012 / F-08 E2). A name-only change has no diff.
    if config_diff is not None:
        diff_before, diff_after = config_diff
        await write_audit(
            session,
            actor_id=admin.id,
            action="area.config.update",
            area_id=area_id,
            before=diff_before,
            after=diff_after,
            ip=_client_ip(request),
            cross_area_bypass=True,
        )
    await session.commit()
    return AreaRead.model_validate(area)


@router.post("/{area_id}/archive", response_model=AreaRead)
async def archive_area(
    area_id: int,
    admin: PlatformAdmin,
    request: Request,
    session: SessionDep,
) -> AreaRead:
    area = await service.archive_area(session, area_id)
    await _audit_bypass(
        session,
        actor=admin,
        action="area.archive",
        area_id=area_id,
        request=request,
        after={"deleted_at": area.deleted_at.isoformat() if area.deleted_at else None},
    )
    await session.commit()
    return AreaRead.model_validate(area)
