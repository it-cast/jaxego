"""Teams service — area-scoped CRUD; credenciais do responsável na própria tabela."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.security import hash_password
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


async def _assert_email_free(session: AsyncSession, email: str, *, exclude_id: int | None = None) -> None:
    stmt = select(Team.id).where(Team.email == email)
    if exclude_id is not None:
        stmt = stmt.where(Team.id != exclude_id)
    if (await session.execute(stmt)).first() is not None:
        raise ValidationAppError("Já existe uma equipe com esse e-mail.")


async def create_team(session: AsyncSession, body: TeamCreate, *, area_id: int) -> Team:
    """Cria a equipe com a conta de login do responsável na própria linha."""
    await _assert_email_free(session, body.responsavel_email)
    team = Team(
        name=body.name,
        area_id=area_id,
        cnpj=body.cnpj,
        razao_social=body.razao_social,
        responsavel=body.responsavel,
        responsavel_cpf=body.responsavel_cpf,
        email=body.responsavel_email,
        password_hash=hash_password(body.responsavel_password),
    )
    session.add(team)
    await session.flush()
    return team


async def update_team(session: AsyncSession, team_id: int, body: TeamUpdate, *, area_id: int) -> Team:
    team = await get_team(session, team_id, area_id=area_id)
    if body.name is not None:
        team.name = body.name
    if body.cnpj is not None:
        team.cnpj = body.cnpj
    if body.razao_social is not None:
        team.razao_social = body.razao_social
    if body.responsavel is not None:
        team.responsavel = body.responsavel
    if body.responsavel_cpf is not None:
        team.responsavel_cpf = body.responsavel_cpf
    if body.responsavel_email:
        await _assert_email_free(session, body.responsavel_email, exclude_id=team.id)
        team.email = body.responsavel_email
    if body.responsavel_password:
        team.password_hash = hash_password(body.responsavel_password)
    await session.flush()
    return team


async def archive_team(session: AsyncSession, team_id: int, *, area_id: int) -> Team:
    team = await get_team(session, team_id, area_id=area_id)
    team.deleted_at = datetime.now(UTC)
    await session.flush()
    return team


async def get_responsavel_email(session: AsyncSession, team: Team) -> str | None:
    return team.email
