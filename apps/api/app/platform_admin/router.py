"""/v1/platform — platform-admin cross-area endpoints (REQ-046/047 / D-06/D-07).

Every route requires `require_platform_admin` (TOTP already enforced — ADR-005; a
platform admin without TOTP enrolled is blocked by `get_current_user`). The reads are
cross-area and AUDITED in the service (TH-02). Revenue-share config is parametrised only
— NO money moves (D-07). Filters are bound by Pydantic/Query (TH-06).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import PlatformAdmin
from app.core.exceptions import NotFoundError
from app.db.session import get_session
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
