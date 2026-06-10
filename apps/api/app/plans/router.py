"""/v1/plans — public catalog of subscription plans (values from SEED, DRV-009).

Thin router: reads the catalog and projects the SEED values. The wizard (step 4)
and the plan screen (tela 16) consume this; NO plan value is hardcoded client-side.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.merchants.schemas import PlanRead
from app.plans import service

router = APIRouter(prefix="/plans", tags=["plans"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[PlanRead])
async def list_plans(session: SessionDep) -> list[PlanRead]:
    """Return the active plans with their SEED values (single query, no N+1)."""
    plans = await service.list_active_plans(session)
    return [
        PlanRead(
            codename=p.code,
            nome=p.name,
            preco_cents=p.price_cents,
            entregas_mes=p.deliveries_per_month,
            taxa_entrega_cents=p.fee_cents,
            is_free=p.is_free,
            is_unlimited=p.is_unlimited,
        )
        for p in plans
    ]
