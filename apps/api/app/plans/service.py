"""Plans service — read catalog + idempotent seed of the 4 plans (DRV-009).

`PLAN_SEEDS` carries the `[ASSUMIDO]` values (price/deliveries/fee) as SEED data:
they are inserted into `subscription_plans` and read back from the DB by the API,
so NO plan value is ever hardcoded in a code path that serves the UI (DRV-009).
`seed_plans_if_missing` upserts by the natural key `code` (idempotent — Pitfall 4).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.plans.models import SubscriptionPlan

# [ASSUMIDO] seed values (DRV-009) — editable seed data, never hardcoded in UI.
# price_monthly_cents / price_annual_cents / fee_cents are integer cents.
# Free is immutable (is_free=True). Annual = monthly × 10 (2 months free).
# taxa_pix_cents: taxa por operação PIX; taxa_servico_cents: taxa de serviço por entrega.
PLAN_SEEDS: tuple[dict[str, object], ...] = (
    {
        "code": "free",
        "name": "Básico",
        "price_monthly_cents": 0,
        "price_annual_cents": 0,
        "deliveries_per_month": 0,
        "fee_cents": 100,
        "taxa_pix_cents": 50,
        "taxa_servico_cents": 100,
        "is_free": True,
        "is_unlimited": True,
        "sort_order": 0,
    },
    {
        "code": "pro",
        "name": "Pro",
        "price_monthly_cents": 2990,
        "price_annual_cents": 29900,
        "deliveries_per_month": 0,
        "fee_cents": 0,
        "taxa_pix_cents": 50,
        "taxa_servico_cents": 0,
        "is_free": False,
        "is_unlimited": True,
        "sort_order": 1,
    },
)

# Códigos dos planos antigos que devem ser desativados ao rodar o seed.
_LEGACY_PLAN_CODES = frozenset({"inicio", "profissional", "sem_limite"})


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


async def list_all_plans(session: AsyncSession) -> list[SubscriptionPlan]:
    stmt = select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order)
    return list((await session.execute(stmt)).scalars().all())


async def get_plan_by_id(session: AsyncSession, plan_id: int) -> SubscriptionPlan:
    stmt = select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    plan = (await session.execute(stmt)).scalar_one_or_none()
    if plan is None:
        raise NotFoundError("Plano não encontrado.")
    return plan


async def create_plan(
    session: AsyncSession,
    *,
    code: str,
    name: str,
    price_monthly_cents: int,
    price_annual_cents: int,
    deliveries_per_month: int,
    fee_cents: int = 0,
    taxa_pix_cents: int = 0,
    taxa_servico_cents: int = 0,
    is_unlimited: bool,
    sort_order: int,
) -> SubscriptionPlan:
    existing = await get_plan_by_code(session, code)
    if existing is not None:
        raise ValidationAppError(f"Já existe um plano com o código '{code}'.")
    plan = SubscriptionPlan(
        code=code,
        name=name,
        price_monthly_cents=price_monthly_cents,
        price_annual_cents=price_annual_cents,
        deliveries_per_month=deliveries_per_month,
        fee_cents=fee_cents,
        taxa_pix_cents=taxa_pix_cents,
        taxa_servico_cents=taxa_servico_cents,
        is_free=False,
        is_unlimited=is_unlimited,
        is_active=True,
        sort_order=sort_order,
    )
    session.add(plan)
    await session.flush()
    return plan


async def update_plan(
    session: AsyncSession,
    plan_id: int,
    *,
    name: str | None = None,
    price_monthly_cents: int | None = None,
    price_annual_cents: int | None = None,
    deliveries_per_month: int | None = None,
    fee_cents: int | None = None,
    taxa_pix_cents: int | None = None,
    taxa_servico_cents: int | None = None,
    is_unlimited: bool | None = None,
    is_active: bool | None = None,
    sort_order: int | None = None,
) -> SubscriptionPlan:
    plan = await get_plan_by_id(session, plan_id)
    if plan.is_free:
        raise ValidationAppError("O plano Básico é imutável e não pode ser editado.")
    if name is not None:
        plan.name = name
    if price_monthly_cents is not None:
        plan.price_monthly_cents = price_monthly_cents
    if price_annual_cents is not None:
        plan.price_annual_cents = price_annual_cents
    if deliveries_per_month is not None:
        plan.deliveries_per_month = deliveries_per_month
    if fee_cents is not None:
        plan.fee_cents = fee_cents
    if taxa_pix_cents is not None:
        plan.taxa_pix_cents = taxa_pix_cents
    if taxa_servico_cents is not None:
        plan.taxa_servico_cents = taxa_servico_cents
    if is_unlimited is not None:
        plan.is_unlimited = is_unlimited
    if is_active is not None:
        plan.is_active = is_active
    if sort_order is not None:
        plan.sort_order = sort_order
    await session.flush()
    return plan


async def delete_plan(session: AsyncSession, plan_id: int) -> None:
    plan = await get_plan_by_id(session, plan_id)
    if plan.is_free:
        raise ValidationAppError("O plano Free não pode ser removido.")
    plan.is_active = False
    await session.flush()


async def seed_plans_if_missing(session: AsyncSession) -> None:
    """Idempotent upsert of active plans by natural key `code` (Pitfall 4).
    Legacy plan codes in _LEGACY_PLAN_CODES are deactivated if they exist."""
    for seed in PLAN_SEEDS:
        existing = await get_plan_by_code(session, str(seed["code"]))
        if existing is None:
            session.add(SubscriptionPlan(**seed))  # type: ignore[arg-type]
        else:
            existing.name = str(seed["name"])
            existing.is_unlimited = bool(seed["is_unlimited"])
            existing.sort_order = int(seed["sort_order"])  # type: ignore[arg-type]
            existing.taxa_pix_cents = int(seed["taxa_pix_cents"])  # type: ignore[arg-type]
            existing.taxa_servico_cents = int(seed["taxa_servico_cents"])  # type: ignore[arg-type]
            if not existing.is_free:
                existing.price_monthly_cents = int(seed["price_monthly_cents"])  # type: ignore[arg-type]
                existing.price_annual_cents = int(seed["price_annual_cents"])  # type: ignore[arg-type]
                existing.deliveries_per_month = int(seed["deliveries_per_month"])  # type: ignore[arg-type]
                existing.fee_cents = int(seed["fee_cents"])  # type: ignore[arg-type]
            existing.is_active = True
    # Deactivate legacy plans no longer in the active seed.
    from sqlalchemy import select as _select
    legacy_stmt = _select(SubscriptionPlan).where(
        SubscriptionPlan.code.in_(_LEGACY_PLAN_CODES)
    )
    legacy_plans = (await session.execute(legacy_stmt)).scalars().all()
    for lp in legacy_plans:
        lp.is_active = False
    await session.flush()
