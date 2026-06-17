"""Areas service + RBAC role resolution.

CRUD is restricted to the platform admin (enforced by the router dependency).
Reads are scoped via the base repository (`WHERE area_id`); a cross-area resource
returns 404 (not 403) so existence is not leaked (A01). Soft-archive replaces
hard delete when an area has dependents (REQ-002, DRV-002).

`resolve_role` is the single authority that maps (user, area) -> role for this
phase (only `area_admins` memberships exist now; merchant_users/couriers arrive
in later phases). Platform admins resolve to 'admin_plataforma' regardless of
area (D-09).
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.config_schema import AreaConfig, diff_sensitive
from app.areas.models import Area, AreaAdmin
from app.areas.schemas import AreaCreate, AreaUpdate
from app.auth.models import User
from app.core.exceptions import AppError, NotFoundError, ValidationAppError

logger = structlog.get_logger("areas")

PLATFORM_ADMIN_ROLE = "admin_plataforma"


class DuplicateAreaError(AppError):
    """An area with the same codename already exists (anti-duplicidade)."""

    status_code = 409
    code = "duplicate_area"

    def __init__(self) -> None:
        super().__init__("Já existe uma área com esse identificador.")


class AreaHasDependentsError(AppError):
    """An area with dependents cannot be deleted — archive it instead (REQ-002)."""

    status_code = 409
    code = "area_has_dependents"

    def __init__(self) -> None:
        super().__init__("Área possui registros vinculados; arquive em vez de excluir.")


def resolve_role(user: User, *, area_id: int | None) -> str:
    """Resolve the user's role in the given area context (D-09).

    Platform admins are 'admin_plataforma' everywhere. Otherwise the role is
    derived from the user's `area_admins` membership for that area, if any.
    NOTE: membership lookup uses the eagerly-loaded `_memberships` cache set by
    the dependency layer to avoid a query here; falls back to 'user'.
    """
    if user.platform_role == PLATFORM_ADMIN_ROLE:
        return PLATFORM_ADMIN_ROLE
    memberships: list[AreaAdmin] = getattr(user, "_memberships", []) or []
    if area_id is not None:
        for m in memberships:
            if m.area_id == area_id:
                return f"admin_area:{m.role}"
    return "user"


async def load_memberships(session: AsyncSession, user: User) -> list[AreaAdmin]:
    """Load and cache the user's area memberships (single query, no N+1)."""
    stmt = select(AreaAdmin).where(AreaAdmin.user_id == user.id)
    memberships = list((await session.execute(stmt)).scalars().all())
    user._memberships = memberships  # type: ignore[attr-defined]
    return memberships


async def create_area(session: AsyncSession, body: AreaCreate) -> Area:
    """Create an area; reject duplicate codename (anti-duplicidade)."""
    existing = (
        await session.execute(select(Area).where(Area.codename == body.codename))
    ).scalar_one_or_none()
    if existing is not None:
        raise DuplicateAreaError()
    area = Area(codename=body.codename, name=body.name, config=body.config)
    session.add(area)
    await session.flush()
    return area


async def get_area(session: AsyncSession, area_id: int) -> Area:
    """Fetch an area by id or raise 404."""
    area = await session.get(Area, area_id)
    if area is None or area.deleted_at is not None:
        raise NotFoundError("Área não encontrada.")
    return area


async def list_areas(session: AsyncSession, *, limit: int = 100, offset: int = 0) -> list[Area]:
    """List non-archived areas (platform-admin view; single query, no N+1)."""
    stmt = (
        select(Area).where(Area.deleted_at.is_(None)).order_by(Area.id).limit(limit).offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all())


async def update_area(
    session: AsyncSession, area_id: int, body: AreaUpdate
) -> tuple[Area, tuple[dict, dict] | None]:
    """Patch an area's mutable fields; return (area, sensitive_config_diff).

    Config is validated through the typed `AreaConfig` (ranges enforced — a value
    out of range raises 422 RFC-7807, never persisted) instead of being written
    raw (Pitfall 4). When a SENSITIVE config key changes, the returned diff lets
    the router record a `write_audit("area.config.update", before, after)` row
    (RN-012 / F-08 E2). `name`-only changes return a None diff.
    """
    area = await get_area(session, area_id)
    if body.name is not None:
        area.name = body.name

    diff: tuple[dict, dict] | None = None
    if body.config is not None:
        try:
            validated = AreaConfig(**body.config)
        except ValidationError as exc:
            # Out-of-range / unknown key → 422 (mapped to the global RFC-7807 envelope).
            raise ValidationAppError(
                "Configuração da área inválida (verifique faixas e chaves)."
            ) from exc
        before_config = dict(area.config or {})
        new_config = validated.model_dump(mode="json")
        diff = diff_sensitive(before_config, new_config)
        area.config = new_config

    await session.flush()
    return area, diff


async def archive_area(session: AsyncSession, area_id: int) -> Area:
    """Soft-archive an area (DRV-002 / REQ-002) — never hard-deleted."""
    area = await get_area(session, area_id)
    area.deleted_at = datetime.now(UTC)  # AWARE — TD-010
    await session.flush()
    return area


class AdminUserNotFoundError(NotFoundError):
    """No user with the given e-mail to assign as area admin (F3.3)."""

    def __init__(self) -> None:
        super().__init__("Nenhum usuário com esse e-mail. Peça para a pessoa criar a conta antes.")


async def assign_area_admin(
    session: AsyncSession, *, area_id: int, user_email: str, role: str
) -> tuple[AreaAdmin, str]:
    """Link a user (by e-mail) to an area as admin, or update the role if it
    already exists. The area must exist (404 otherwise). Returns (membership, email)."""
    await get_area(session, area_id)  # 404 if missing/archived
    user = (
        await session.execute(select(User).where(User.email == user_email))
    ).scalar_one_or_none()
    if user is None:
        raise AdminUserNotFoundError()
    membership = (
        await session.execute(
            select(AreaAdmin).where(AreaAdmin.area_id == area_id, AreaAdmin.user_id == user.id)
        )
    ).scalar_one_or_none()
    if membership is None:
        membership = AreaAdmin(area_id=area_id, user_id=user.id, role=role)
        session.add(membership)
        await session.flush()
    else:
        membership.role = role
    return membership, user.email
