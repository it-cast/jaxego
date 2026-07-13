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
from app.areas.models import Area, AreaAdmin, Zona
from app.areas.schemas import AreaCreate, AreaUpdate, ZonaCreate, ZonaUpdate
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
        # Merge: preserve unknown legacy fields, overwrite only the validated ones.
        new_config = {**before_config, **validated.model_dump(mode="json")}
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
    """No area admin account with the given e-mail (F3.3)."""

    def __init__(self) -> None:
        super().__init__("Nenhum admin com esse e-mail. Crie a conta de admin antes.")


async def assign_area_admin(
    session: AsyncSession, *, area_id: int, user_email: str, role: str
) -> tuple[AreaAdmin, str]:
    """Move/atualiza uma conta de admin (por e-mail) para a área com o role dado."""
    await get_area(session, area_id)  # 404 if missing/archived
    admin = (
        await session.execute(select(AreaAdmin).where(AreaAdmin.email == user_email))
    ).scalar_one_or_none()
    if admin is None:
        raise AdminUserNotFoundError()
    admin.area_id = area_id
    admin.role = role
    await session.flush()
    return admin, admin.email or ""


async def list_area_admins(session: AsyncSession) -> list[dict]:
    """All area admin accounts with area name (single query)."""
    stmt = (
        select(AreaAdmin, Area.name.label("area_name"))
        .join(Area, AreaAdmin.area_id == Area.id)
        .order_by(AreaAdmin.area_id, AreaAdmin.id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": m.id,
            "area_id": m.area_id,
            "area_name": area_name,
            "user_id": m.id,
            "user_email": m.email,
            "user_name": m.name,
            "role": m.role,
        }
        for m, area_name in rows
    ]


async def create_area_admin_with_user(
    session: AsyncSession,
    *,
    area_id: int,
    email: str,
    name: str,
    password_hash: str,
    role: str,
) -> AreaAdmin:
    """Cria a conta do admin da cidade (credenciais na própria tabela)."""
    from app.core.exceptions import ValidationAppError

    await get_area(session, area_id)
    existing = (
        await session.execute(select(AreaAdmin).where(AreaAdmin.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        raise ValidationAppError(f"'{email}' ja e admin de uma area.")
    admin = AreaAdmin(
        area_id=area_id, email=email, name=name, password_hash=password_hash, role=role
    )
    session.add(admin)
    await session.flush()
    return admin


async def update_area_admin(
    session: AsyncSession,
    admin_id: int,
    *,
    role: str | None = None,
    area_id: int | None = None,
    name: str | None = None,
    email: str | None = None,
    password_hash: str | None = None,
) -> AreaAdmin:
    membership = await session.get(AreaAdmin, admin_id)
    if membership is None:
        raise NotFoundError("Admin de area nao encontrado.")
    if role is not None:
        membership.role = role
    if area_id is not None:
        await get_area(session, area_id)
        membership.area_id = area_id
    if name is not None:
        membership.name = name
    if email is not None:
        dup = (
            await session.execute(
                select(AreaAdmin.id).where(AreaAdmin.email == email, AreaAdmin.id != admin_id)
            )
        ).first()
        if dup is not None:
            raise ValidationAppError(f"'{email}' ja e admin de uma area.")
        membership.email = email
    if password_hash is not None:
        membership.password_hash = password_hash
    await session.flush()
    return membership


async def remove_area_admin(session: AsyncSession, admin_id: int) -> None:
    membership = await session.get(AreaAdmin, admin_id)
    if membership is None:
        raise NotFoundError("Admin de area nao encontrado.")
    await session.delete(membership)
    await session.flush()


# ---------------------------------------------------------------------------
# Zona CRUD (admin_area scoped)
# ---------------------------------------------------------------------------

async def list_zonas(session: AsyncSession, area_id: int) -> list[Zona]:
    stmt = select(Zona).where(Zona.area_id == area_id).order_by(Zona.id)
    return list((await session.execute(stmt)).scalars().all())


async def create_zona(session: AsyncSession, area_id: int, body: ZonaCreate) -> Zona:
    zona = Zona(area_id=area_id, name=body.name, boundary=body.boundary)
    session.add(zona)
    await session.flush()

    # Link all existing active couriers in the area to this new zone (ativo=False).
    from app.couriers.models import Courier, CourierZona

    couriers = list(
        (
            await session.execute(
                select(Courier).where(
                    Courier.area_id == area_id,
                    Courier.deleted_at.is_(None),
                )
            )
        ).scalars().all()
    )
    for c in couriers:
        session.add(CourierZona(
            area_id=area_id,
            courier_id=c.id,
            zona_id=zona.id,
            ativo=False,
            preco_cents=0,
        ))
    if couriers:
        await session.flush()

    return zona


async def update_zona(
    session: AsyncSession, zona_id: int, area_id: int, body: ZonaUpdate
) -> Zona:
    zona = await session.get(Zona, zona_id)
    if zona is None or zona.area_id != area_id:
        raise NotFoundError("Zona não encontrada.")
    if body.name is not None:
        zona.name = body.name
    if body.boundary is not None:
        zona.boundary = body.boundary
    await session.flush()
    return zona


async def delete_zona(session: AsyncSession, zona_id: int, area_id: int) -> None:
    zona = await session.get(Zona, zona_id)
    if zona is None or zona.area_id != area_id:
        raise NotFoundError("Zona não encontrada.")
    await session.delete(zona)
    await session.flush()
