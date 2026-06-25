"""Teams service — area-scoped CRUD."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.teams.models import Team
from app.teams.schemas import TeamCreate, TeamUpdate


async def list_teams(
    session: AsyncSession, *, area_id: int, limit: int = 20, offset: int = 0
) -> tuple[list[Team], int]:
    from sqlalchemy import func
    base = select(Team).where(Team.area_id == area_id, Team.deleted_at.is_(None))
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    rows = list(
        (await session.execute(base.order_by(Team.id).limit(limit).offset(offset))).scalars().all()
    )
    return rows, total


async def get_team(session: AsyncSession, team_id: int, *, area_id: int) -> Team:
    team = await session.get(Team, team_id)
    if team is None or team.area_id != area_id or team.deleted_at is not None:
        raise NotFoundError("Equipe não encontrada.")
    return team


async def create_team(session: AsyncSession, body: TeamCreate, *, area_id: int) -> Team:
    team = Team(name=body.name, area_id=area_id)
    session.add(team)
    await session.flush()
    return team


async def update_team(session: AsyncSession, team_id: int, body: TeamUpdate, *, area_id: int) -> Team:
    team = await get_team(session, team_id, area_id=area_id)
    if body.name is not None:
        team.name = body.name
    await session.flush()
    return team


async def archive_team(session: AsyncSession, team_id: int, *, area_id: int) -> Team:
    team = await get_team(session, team_id, area_id=area_id)
    team.deleted_at = datetime.now(UTC)
    await session.flush()
    return team
