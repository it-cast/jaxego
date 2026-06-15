"""/v1/platform/disputes — platform-admin financial decision (Phase 15 — REQ-039).

The platform admin decides a dispute `procedente` | `improcedente`. A `procedente`
decision issues a refund/credit via the `PaymentPort` and counts toward RN-027 (2/30d →
90-day block). Every decision is AUDITED in the service (TH-05). TOTP-gated via
`require_platform_admin` (ADR-005). The decision is cross-area; the route resolves the
dispute by id with the area taken from the dispute row itself (a platform admin acts
across areas — the audit records the action).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import PlatformAdmin
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.payments.factory import get_payment_adapter
from app.payments_direct import disputes
from app.payments_direct.models import PaymentDispute

router = APIRouter(prefix="/platform/disputes", tags=["platform-disputes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class DecideIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = Field(pattern=r"^(procedente|improcedente)$")


class DecideOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dispute_id: int
    decision: str
    adjustment_cents: int
    blocked: bool


@router.post("/{dispute_id}/decide", response_model=DecideOut)
async def decide(
    dispute_id: int, body: DecideIn, admin: PlatformAdmin, session: SessionDep
) -> DecideOut:
    """Decide a dispute financially (D-03). procedente → refund/credit + maybe block."""
    # Resolve the dispute's area (platform-admin is cross-area; service audits the action).
    dispute = (
        (await session.execute(select(PaymentDispute).where(PaymentDispute.id == dispute_id)))
        .scalars()
        .first()
    )
    if dispute is None:
        raise NotFoundError("Disputa não encontrada.")

    decided, block = await disputes.decide_dispute(
        session,
        dispute_id=dispute_id,
        area_id=dispute.area_id,
        decision=body.decision,
        actor_id=admin.id,
        payment=get_payment_adapter(),
    )
    await session.commit()
    return DecideOut(
        dispute_id=decided.id,
        decision=decided.decision or body.decision,
        adjustment_cents=decided.adjustment_cents or 0,
        blocked=block is not None,
    )


__all__ = ["router"]
