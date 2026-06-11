"""/v1/withdrawals — courier balance + withdrawal request (Phase 15 — REQ-038, tela 16).

All routes are scoped to the authenticated courier via `courier_scope` (A01 / TH-01 —
IDOR closed in the WHERE clause). The repasse goes through the `PaymentPort.payout` (Stub
in dev/test — D-09); a failed payout restores the balance (D-04). The reference is
server-derived so the same courier+amount cannot be replayed to double-spend within a
request (TH-02); idempotency is also enforced by the UNIQUE reference.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.dispatch.dependencies import CourierScopeDep
from app.payments.factory import get_payment_adapter
from app.withdrawals import service

router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class BalanceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    balance_cents: int
    minimum_cents: int


class WithdrawalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount_cents: int = Field(ge=1)
    # Client-supplied idempotency key (optional); the server prefixes the courier scope.
    idempotency_key: str | None = Field(default=None, max_length=40)


class WithdrawalOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    amount_cents: int
    status: str
    transaction_id: str | None


@router.get("/balance", response_model=BalanceOut)
async def get_balance(scope: CourierScopeDep, session: SessionDep) -> BalanceOut:
    """The courier's withdrawable balance + the minimum (scoped to the courier — TH-01)."""
    from app.core.config import settings

    balance = await service.available_balance(
        session, area_id=scope.area_id, courier_id=scope.courier_id
    )
    return BalanceOut(balance_cents=balance, minimum_cents=settings.withdrawal_min_cents)


@router.post("", response_model=WithdrawalOut)
async def request_withdrawal(
    body: WithdrawalIn, scope: CourierScopeDep, session: SessionDep
) -> WithdrawalOut:
    """Request a withdrawal of the released escrow balance (D-04 / TH-01/TH-02)."""
    key = body.idempotency_key or f"{int(datetime.now(UTC).timestamp())}"
    reference = f"wd_{scope.courier_id}_{key}"
    withdrawal = await service.request_withdrawal(
        session,
        area_id=scope.area_id,
        courier_id=scope.courier_id,
        amount_cents=body.amount_cents,
        reference=reference,
        payment=get_payment_adapter(),
    )
    await session.commit()
    return WithdrawalOut(
        id=withdrawal.id,
        amount_cents=withdrawal.amount_cents,
        status=withdrawal.status,
        transaction_id=withdrawal.transaction_id,
    )


__all__ = ["router"]
