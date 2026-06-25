"""/v1/admin/teams — area-admin team CRUD (equipes).

Scoped to the admin's area via AreaScopeDep. Only area admins can manage teams.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, require_role
from app.auth.models import User
from app.db.session import get_session
from app.teams import service
from app.teams.schemas import TeamCreate, TeamRead, TeamUpdate

router = APIRouter(prefix="/admin/teams", tags=["admin-teams"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AreaAdminDep = Annotated[User, Depends(require_role("admin_area"))]


@router.get("")
async def list_teams(
    admin: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    teams, total = await service.list_teams(session, area_id=scope, limit=limit, offset=offset)
    return {
        "items": [TeamRead.model_validate(t) for t in teams],
        "total": total,
    }


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreate,
    admin: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> TeamRead:
    team = await service.create_team(session, body, area_id=scope)
    await session.commit()
    return TeamRead.model_validate(team)


@router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: int,
    body: TeamUpdate,
    admin: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> TeamRead:
    team = await service.update_team(session, team_id, body, area_id=scope)
    await session.commit()
    return TeamRead.model_validate(team)


@router.post("/{team_id}/archive", response_model=TeamRead)
async def archive_team(
    team_id: int,
    admin: AreaAdminDep,
    scope: AreaScopeDep,
    session: SessionDep,
) -> TeamRead:
    team = await service.archive_team(session, team_id, area_id=scope)
    await session.commit()
    return TeamRead.model_validate(team)
