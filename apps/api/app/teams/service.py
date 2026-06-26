"""Teams service — area-scoped CRUD with user creation for the responsible."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
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


async def create_team(session: AsyncSession, body: TeamCreate, *, area_id: int) -> Team:
    existing_user = (await session.execute(
        select(User).where(User.email == body.responsavel_email)
    )).scalar_one_or_none()
    if existing_user:
        user = existing_user
        user.password_hash = hash_password(body.responsavel_password)
        if not user.cpf:
            user.cpf = body.responsavel_cpf.replace(".", "").replace("-", "")
    else:
        user = User(
            email=body.responsavel_email,
            name=body.responsavel,
            password_hash=hash_password(body.responsavel_password),
            platform_role="user",
            cpf=body.responsavel_cpf.replace(".", "").replace("-", ""),
        )
        session.add(user)
        await session.flush()

    team = Team(
        name=body.name,
        area_id=area_id,
        cnpj=body.cnpj,
        razao_social=body.razao_social,
        responsavel=body.responsavel,
        responsavel_cpf=body.responsavel_cpf,
        responsavel_user_id=user.id,
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
    if body.responsavel_email or body.responsavel_password:
        if team.responsavel_user_id:
            user = await session.get(User, team.responsavel_user_id)
            if user:
                if body.responsavel_email:
                    user.email = body.responsavel_email
                if body.responsavel_password:
                    user.password_hash = hash_password(body.responsavel_password)
        elif body.responsavel_email and body.responsavel_password:
            existing = (await session.execute(
                select(User).where(User.email == body.responsavel_email)
            )).scalar_one_or_none()
            if existing:
                team.responsavel_user_id = existing.id
                if body.responsavel_password:
                    existing.password_hash = hash_password(body.responsavel_password)
            else:
                user = User(
                    email=body.responsavel_email,
                    name=team.responsavel,
                    password_hash=hash_password(body.responsavel_password),
                    platform_role="user",
                    cpf=(body.responsavel_cpf or team.responsavel_cpf).replace(".", "").replace("-", "") or None,
                )
                session.add(user)
                await session.flush()
                team.responsavel_user_id = user.id
    await session.flush()
    return team


async def archive_team(session: AsyncSession, team_id: int, *, area_id: int) -> Team:
    team = await get_team(session, team_id, area_id=area_id)
    team.deleted_at = datetime.now(UTC)
    await session.flush()
    return team


async def get_responsavel_email(session: AsyncSession, team: Team) -> str | None:
    if not team.responsavel_user_id:
        return None
    user = await session.get(User, team.responsavel_user_id)
    return user.email if user else None
