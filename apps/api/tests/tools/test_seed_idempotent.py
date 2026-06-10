"""REQ-009 — seed.py idempotente: rodar 2x não duplica (Pitfall 4)."""

from __future__ import annotations

import pytest
from app.areas.models import Area
from app.auth.models import User
from app.plans.models import SubscriptionPlan
from sqlalchemy import func, select

from tools.seed import run_seed


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session) -> None:
    await run_seed(db_session)
    await db_session.commit()
    await run_seed(db_session)
    await db_session.commit()

    # Exactly one Pádua area.
    padua = (
        await db_session.execute(
            select(func.count()).select_from(Area).where(Area.codename == "padua")
        )
    ).scalar_one()
    assert padua == 1

    # Exactly 4 plans.
    plans = (
        await db_session.execute(select(func.count()).select_from(SubscriptionPlan))
    ).scalar_one()
    assert plans == 4

    # Platform admin + area admin de-duplicated by email.
    plat = (
        await db_session.execute(
            select(func.count()).select_from(User).where(User.platform_role == "admin_plataforma")
        )
    ).scalar_one()
    assert plat == 1


@pytest.mark.asyncio
async def test_seed_creates_free_plan_immutable_flag(db_session) -> None:
    await run_seed(db_session)
    await db_session.commit()
    free = (
        await db_session.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "free"))
    ).scalar_one()
    assert free.is_free is True
    assert free.price_cents == 0


@pytest.mark.asyncio
async def test_seed_plan_values_are_data_not_hardcoded(db_session) -> None:
    """All four plan codes exist with seedable values (DRV-009)."""
    await run_seed(db_session)
    await db_session.commit()
    codes = {p.code for p in (await db_session.execute(select(SubscriptionPlan))).scalars().all()}
    assert codes == {"free", "inicio", "profissional", "sem_limite"}
