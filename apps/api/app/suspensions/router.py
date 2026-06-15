"""Area-admin suspension + dispute endpoints (REQ-044/045 / D-04/D-05/D-08).

`admin_router` (/v1/admin/suspensions): the area admin opens a suspension (reason
mandatory → audited), lists the area's appeals, and records an appeal decision
(overturned lifts the suspension). `disputes_router` (/v1/admin/disputes): lists the
area's payment disputes (Phase 9 primitive) and records an ADMINISTRATIVE decision —
NO financial effect (DEC-004 → Phase 15).

All endpoints require `require_role("admin_area")` + `area_scope`; the area is in the
WHERE clause (TH-03 → 404 outside scope). Pagination is by limit/offset (cursor-ready).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
from app.db.session import get_session
from app.suspensions import service
from app.suspensions.schemas import (
    AppealDecisionBody,
    AppealRead,
    DisputeDecisionBody,
    DisputeRead,
    SuspensionCreateBody,
)

admin_router = APIRouter(prefix="/admin/suspensions", tags=["suspensions-admin"])
disputes_router = APIRouter(prefix="/admin/disputes", tags=["disputes-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AdminArea = Annotated[CurrentUser, Depends(require_role("admin_area"))]


# ---------------------------------------------------------------------------
# Suspensions / appeals (REQ-045)
# ---------------------------------------------------------------------------
@admin_router.post("", response_model=AppealRead, status_code=status.HTTP_201_CREATED)
async def open_suspension(
    body: SuspensionCreateBody,
    session: SessionDep,
    admin: AdminArea,
    scope: AreaScopeDep,
) -> AppealRead:
    """Suspend a courier/merchant (reason mandatory → audited) + open the appeal window."""
    appeal = await service.open_suspension(
        session,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        area_id=scope,  # type: ignore[arg-type]
        reason=body.reason,
        actor_id=admin.id,
        cross_area_bypass=False,
    )
    await session.commit()
    return AppealRead.model_validate(appeal)


@admin_router.get("", response_model=list[AppealRead])
async def list_appeals(
    session: SessionDep,
    admin: AdminArea,
    scope: AreaScopeDep,
    open_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AppealRead]:
    """List the area's suspension appeals (open or all)."""
    appeals = await service.list_appeals(
        session, area_id=scope, open_only=open_only, limit=limit, offset=offset
    )
    return [AppealRead.model_validate(a) for a in appeals]


@admin_router.patch("/{appeal_id}/decision", response_model=AppealRead)
async def decide_appeal(
    appeal_id: int,
    body: AppealDecisionBody,
    session: SessionDep,
    admin: AdminArea,
    scope: AreaScopeDep,
) -> AppealRead:
    """Record the appeal decision; `overturned` lifts the suspension (audited)."""
    appeal = await service.decide_appeal(
        session,
        appeal_id=appeal_id,
        area_id=scope,
        decision=body.decision,
        actor_id=admin.id,
    )
    await session.commit()
    return AppealRead.model_validate(appeal)


# ---------------------------------------------------------------------------
# Disputes (REQ-044 — administrative decision only, NO financial effect)
# ---------------------------------------------------------------------------
@disputes_router.get("", response_model=list[DisputeRead])
async def list_disputes(
    session: SessionDep,
    admin: AdminArea,
    scope: AreaScopeDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[DisputeRead]:
    """List the area's payment disputes (Phase 9 primitive)."""
    disputes = await service.list_disputes(session, area_id=scope, limit=limit, offset=offset)
    return [DisputeRead.model_validate(d) for d in disputes]


@disputes_router.patch("/{dispute_id}/decision", response_model=DisputeRead)
async def decide_dispute(
    dispute_id: int,
    body: DisputeDecisionBody,
    session: SessionDep,
    admin: AdminArea,
    scope: AreaScopeDep,
) -> DisputeRead:
    """Register an administrative dispute decision (audited). NO financial effect (Phase 15)."""
    dispute = await service.record_dispute_decision(
        session,
        dispute_id=dispute_id,
        area_id=scope,
        outcome=body.outcome,
        actor_id=admin.id,
        note=body.note,
    )
    await session.commit()
    return DisputeRead.model_validate(dispute)
