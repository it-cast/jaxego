"""/v1/platform — platform-admin cross-area endpoints (REQ-046/047 / D-06/D-07).

Every route requires `require_platform_admin` (TOTP already enforced — ADR-005; a
platform admin without TOTP enrolled is blocked by `get_current_user`). The reads are
cross-area and AUDITED in the service (TH-02). Revenue-share config is parametrised only
— NO money moves (D-07). Filters are bound by Pydantic/Query (TH-06).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas import service as areas_service
from app.areas.schemas import AreaAdminCreateBody, AreaAdminRead, AreaAdminUpdateBody
from app.auth.dependencies import PlatformAdmin
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.db.session import get_session
from app.plans import service as plans_service
from app.plans.schemas import PlanAdminRead, PlanCreate, PlanUpdate
from app.platform_admin import service
from app.platform_admin.schemas import (
    AreaOverviewRow,
    CourierSearchRow,
    MerchantSearchRow,
    RevenueShareBody,
    RevenueShareRead,
)
from app.suspensions import service as suspensions_service
from app.suspensions.schemas import AppealRead, DisputeRead

router = APIRouter(prefix="/platform", tags=["platform-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/overview", response_model=list[AreaOverviewRow])
async def overview(
    session: SessionDep,
    admin: PlatformAdmin,
) -> list[AreaOverviewRow]:
    """Per-area headline counts (tela 23). Cross-area read → audited."""
    rows = await service.area_overview(session, actor_id=admin.id)
    await session.commit()  # persist the audit row
    return [AreaOverviewRow(**r) for r in rows]


@router.get("/couriers", response_model=list[CourierSearchRow])
async def search_couriers(
    session: SessionDep,
    admin: PlatformAdmin,
    q: str | None = Query(default=None, max_length=120),
    area_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CourierSearchRow]:
    """Cross-area courier search with score (tela 24). Audited."""
    rows = await service.search_couriers(
        session, actor_id=admin.id, q=q, area_id=area_id, limit=limit, offset=offset
    )
    await session.commit()
    return [CourierSearchRow(**r) for r in rows]


@router.get("/merchants", response_model=list[MerchantSearchRow])
async def search_merchants(
    session: SessionDep,
    admin: PlatformAdmin,
    q: str | None = Query(default=None, max_length=120),
    area_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MerchantSearchRow]:
    """Cross-area merchant search (tela 24). Audited."""
    rows = await service.search_merchants(
        session, actor_id=admin.id, q=q, area_id=area_id, limit=limit, offset=offset
    )
    await session.commit()
    return [MerchantSearchRow(**r) for r in rows]


@router.get("/disputes", response_model=list[DisputeRead])
async def global_disputes(
    session: SessionDep,
    admin: PlatformAdmin,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[DisputeRead]:
    """Global (cross-area) payment disputes (tela 25)."""
    disputes = await suspensions_service.list_disputes(
        session, area_id=None, limit=limit, offset=offset
    )
    return [DisputeRead.model_validate(d) for d in disputes]


@router.get("/suspensions", response_model=list[AppealRead])
async def global_suspensions(
    session: SessionDep,
    admin: PlatformAdmin,
    open_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AppealRead]:
    """Global (cross-area) suspension appeals (tela 25)."""
    appeals = await suspensions_service.list_appeals(
        session, area_id=None, open_only=open_only, limit=limit, offset=offset
    )
    return [AppealRead.model_validate(a) for a in appeals]


@router.get("/areas/{area_id}/revenue-share", response_model=RevenueShareRead)
async def get_revenue_share(
    area_id: int,
    session: SessionDep,
    admin: PlatformAdmin,
) -> RevenueShareRead:
    """The area's current parametrised revenue-share % (config only — NO money)."""
    row = await suspensions_service.current_revenue_share(session, area_id=area_id)
    if row is None:
        raise NotFoundError("Configuração de repasse não encontrada.")
    return RevenueShareRead(
        area_id=row.area_id, share_pct=float(row.share_pct), effective_from=row.effective_from
    )


@router.put("/areas/{area_id}/revenue-share", response_model=RevenueShareRead)
async def set_revenue_share(
    area_id: int,
    body: RevenueShareBody,
    session: SessionDep,
    admin: PlatformAdmin,
) -> RevenueShareRead:
    """Set a new effective revenue-share % (audited). NO money moves (D-07/DEC-004)."""
    row = await suspensions_service.set_revenue_share(
        session, area_id=area_id, share_pct=Decimal(str(body.share_pct)), actor_id=admin.id
    )
    await session.commit()
    return RevenueShareRead(
        area_id=row.area_id, share_pct=float(row.share_pct), effective_from=row.effective_from
    )


# --- Plans CRUD (platform admin) -------------------------------------------


@router.get("/plans", response_model=list[PlanAdminRead])
async def list_plans(
    session: SessionDep,
    admin: PlatformAdmin,
) -> list[PlanAdminRead]:
    plans = await plans_service.list_all_plans(session)
    return [PlanAdminRead.model_validate(p) for p in plans]


@router.post("/plans", response_model=PlanAdminRead, status_code=201)
async def create_plan(
    body: PlanCreate,
    session: SessionDep,
    admin: PlatformAdmin,
) -> PlanAdminRead:
    plan = await plans_service.create_plan(
        session,
        code=body.code,
        name=body.name,
        price_monthly_cents=body.price_monthly_cents,
        price_annual_cents=body.price_annual_cents,
        deliveries_per_month=body.deliveries_per_month,
        fee_cents=body.fee_cents,
        taxa_pix_cents=body.taxa_pix_cents,
        taxa_servico_cents=body.taxa_servico_cents,
        is_unlimited=body.is_unlimited,
        sort_order=body.sort_order,
    )
    await session.commit()
    return PlanAdminRead.model_validate(plan)


@router.patch("/plans/{plan_id}", response_model=PlanAdminRead)
async def update_plan(
    plan_id: int,
    body: PlanUpdate,
    session: SessionDep,
    admin: PlatformAdmin,
) -> PlanAdminRead:
    plan = await plans_service.update_plan(
        session,
        plan_id,
        name=body.name,
        price_monthly_cents=body.price_monthly_cents,
        price_annual_cents=body.price_annual_cents,
        deliveries_per_month=body.deliveries_per_month,
        fee_cents=body.fee_cents,
        taxa_pix_cents=body.taxa_pix_cents,
        taxa_servico_cents=body.taxa_servico_cents,
        is_unlimited=body.is_unlimited,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    await session.commit()
    return PlanAdminRead.model_validate(plan)


@router.delete("/plans/{plan_id}", status_code=204, response_class=Response)
async def delete_plan(
    plan_id: int,
    session: SessionDep,
    admin: PlatformAdmin,
) -> Response:
    await plans_service.delete_plan(session, plan_id)
    await session.commit()
    return Response(status_code=204)


# --- Area Admins CRUD (platform admin) --------------------------------------


@router.get("/area-admins", response_model=list[AreaAdminRead])
async def list_area_admins(
    session: SessionDep,
    admin: PlatformAdmin,
) -> list[AreaAdminRead]:
    rows = await areas_service.list_area_admins(session)
    return [AreaAdminRead(**r) for r in rows]


@router.post("/area-admins", response_model=AreaAdminRead, status_code=201)
async def create_area_admin(
    body: AreaAdminCreateBody,
    session: SessionDep,
    admin: PlatformAdmin,
) -> AreaAdminRead:
    membership = await areas_service.create_area_admin_with_user(
        session,
        area_id=body.area_id,
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    await session.commit()
    rows = await areas_service.list_area_admins(session)
    match = next((r for r in rows if r["id"] == membership.id), None)
    if match is None:
        raise NotFoundError("Admin criado mas nao encontrado.")
    return AreaAdminRead(**match)


@router.patch("/area-admins/{admin_id}", response_model=AreaAdminRead)
async def update_area_admin(
    admin_id: int,
    body: AreaAdminUpdateBody,
    session: SessionDep,
    admin: PlatformAdmin,
) -> AreaAdminRead:
    await areas_service.update_area_admin(
        session,
        admin_id,
        role=body.role,
        area_id=body.area_id,
        name=body.name,
        email=str(body.email) if body.email else None,
        password_hash=hash_password(body.password) if body.password else None,
    )
    await session.commit()
    rows = await areas_service.list_area_admins(session)
    match = next((r for r in rows if r["id"] == admin_id), None)
    if match is None:
        raise NotFoundError("Admin nao encontrado.")
    return AreaAdminRead(**match)


@router.delete("/area-admins/{admin_id}", status_code=204, response_class=Response)
async def remove_area_admin(
    admin_id: int,
    session: SessionDep,
    admin: PlatformAdmin,
) -> Response:
    await areas_service.remove_area_admin(session, admin_id)
    await session.commit()
    return Response(status_code=204)
