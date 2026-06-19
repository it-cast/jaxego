"""Idempotent bootstrap seed (D-09): área Pádua + 4 planos + admins.

Upserts by NATURAL KEY (area by `codename`, plan by `code`, user by `email`) so
running it twice never duplicates (Pitfall 4 / REQ-009). Plan VALUES come from
`app.plans.service.PLAN_SEEDS` (DRV-009 — editable seed data, never hardcoded in
a serving code path). Admin passwords are argon2id (`auth/`).

Usage (against the configured DATABASE_URL):
    uv run python -m tools.seed
"""

from __future__ import annotations

import asyncio

import structlog
from app.areas.models import Area, AreaAdmin
from app.auth.models import User
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.plans.service import seed_plans_if_missing
from app.scores.service import seed_weights_if_missing
from app.suspensions.service import seed_revenue_share_if_missing
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger("seed")

PADUA_CODENAME = "padua"
PLATFORM_ADMIN_EMAIL = "admin@jaxego.com.br"
AREA_ADMIN_EMAIL = "padua.admin@jaxego.com.br"

# Bootstrap default password (dev only). In staging/production rotate immediately;
# this is a documented bootstrap step, not a committed secret for a real account.
_BOOTSTRAP_PASSWORD = "trocar-esta-senha-10"


async def _upsert_area(session: AsyncSession) -> Area:
    existing = (
        await session.execute(select(Area).where(Area.codename == PADUA_CODENAME))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    area = Area(
        codename=PADUA_CODENAME,
        name="Santo Antônio de Pádua",
        config={
            "kyc_level": "simples",
            "bbox": {"min_lat": -21.70, "max_lat": -21.40, "min_lng": -42.25, "max_lng": -41.85},
        },
    )
    session.add(area)
    await session.flush()
    return area


async def _upsert_user(session: AsyncSession, *, email: str, name: str, platform_role: str) -> User:
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        return existing
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(_BOOTSTRAP_PASSWORD),
        platform_role=platform_role,
    )
    session.add(user)
    await session.flush()
    return user


async def _upsert_area_admin(session: AsyncSession, *, area: Area, user: User) -> None:
    existing = (
        await session.execute(
            select(AreaAdmin).where(AreaAdmin.area_id == area.id, AreaAdmin.user_id == user.id)
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(AreaAdmin(area_id=area.id, user_id=user.id, role="owner"))
        await session.flush()


async def run_seed(session: AsyncSession) -> None:
    """Idempotent seed: Pádua + 4 plans + platform admin + area admin."""
    area = await _upsert_area(session)
    await seed_plans_if_missing(session)
    # Phase 13 — parametrised score weights (DRV-009) + [ASSUMIDO] revenue share %.
    await seed_weights_if_missing(session)
    await seed_revenue_share_if_missing(session, area_id=area.id)
    await _upsert_user(
        session,
        email=PLATFORM_ADMIN_EMAIL,
        name="Admin Plataforma",
        platform_role="admin_plataforma",
    )
    area_admin = await _upsert_user(
        session, email=AREA_ADMIN_EMAIL, name="Admin Pádua", platform_role="user"
    )
    await _upsert_area_admin(session, area=area, user=area_admin)
    logger.info("seed_done", area=PADUA_CODENAME)


async def _main() -> None:
    async with async_session_factory() as session:
        await run_seed(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(_main())
