"""Plans service — read catalog + idempotent seed of the 4 plans (DRV-009).

`PLAN_SEEDS` carries the `[ASSUMIDO]` values (price/deliveries/fee) as SEED data:
they are inserted into `subscription_plans` and read back from the DB by the API,
so NO plan value is ever hardcoded in a code path that serves the UI (DRV-009).
`seed_plans_if_missing` upserts by the natural key `code` (idempotent — Pitfall 4).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.plans.models import SubscriptionPlan

# [ASSUMIDO] seed values (DRV-009) — editable seed data, never hardcoded in UI.
# price_cents / fee_cents are integer cents. Free is immutable (is_free=True).
PLAN_SEEDS: tuple[dict[str, object], ...] = (
    {
        "code": "free",
        "name": "Free",
        "price_cents": 0,
        "deliveries_per_month": 2,
        "fee_cents": 200,
        "is_free": True,
        "is_unlimited": False,
        "sort_order": 0,
    },
    {
        "code": "inicio",
        "name": "Início",
        "price_cents": 4900,
        "deliveries_per_month": 40,
        "fee_cents": 150,
        "is_free": False,
        "is_unlimited": False,
        "sort_order": 1,
    },
    {
        "code": "profissional",
        "name": "Profissional",
        "price_cents": 12900,
        "deliveries_per_month": 150,
        "fee_cents": 100,
        "is_free": False,
        "is_unlimited": False,
        "sort_order": 2,
    },
    {
        "code": "sem_limite",
        "name": "Sem Limite",
        "price_cents": 29900,
        "deliveries_per_month": 0,  # 0 == unlimited (is_unlimited flag carries meaning)
        "fee_cents": 50,
        "is_free": False,
        "is_unlimited": True,
        "sort_order": 3,
    },
)


async def list_active_plans(session: AsyncSession) -> list[SubscriptionPlan]:
    """All active plans ordered for display (single query, no N+1)."""
    stmt = (
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.sort_order)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_plan_by_code(session: AsyncSession, code: str) -> SubscriptionPlan | None:
    stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == code)
    return (await session.execute(stmt)).scalar_one_or_none()


async def seed_plans_if_missing(session: AsyncSession) -> None:
    """Idempotent upsert of the 4 plans by natural key `code` (Pitfall 4)."""
    for seed in PLAN_SEEDS:
        existing = await get_plan_by_code(session, str(seed["code"]))
        if existing is None:
            session.add(SubscriptionPlan(**seed))  # type: ignore[arg-type]
        else:
            # Update mutable seed values (Free price stays 0; is_free immutable).
            existing.name = str(seed["name"])
            if not existing.is_free:
                existing.price_cents = int(seed["price_cents"])  # type: ignore[arg-type]
                existing.deliveries_per_month = int(seed["deliveries_per_month"])  # type: ignore[arg-type]
                existing.fee_cents = int(seed["fee_cents"])  # type: ignore[arg-type]
            existing.is_unlimited = bool(seed["is_unlimited"])
            existing.sort_order = int(seed["sort_order"])  # type: ignore[arg-type]
    await session.flush()
