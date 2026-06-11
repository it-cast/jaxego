"""/v1/deliveries/{id}/payment-confirmation — courier confirms direct payment (RN-026).

Only the courier assigned to the delivery may confirm (ownership in the query — TH-7,
reusing `get_delivery_for_courier`). "Não recebi" concludes ENTREGUE (already so) and
opens a `PaymentDispute` (mediação Phase 11). `commit()` in the router.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime

from app.db.session import get_session
from app.deliveries.dependencies import MerchantScopeDep
from app.deliveries.service import get_delivery
from app.dispatch.dependencies import CourierScopeDep
from app.payments_direct.service import (
    confirm_direct_payment,
    get_confirmation_for_delivery,
)
from app.proofs.service import get_delivery_for_courier

router = APIRouter(prefix="/deliveries", tags=["payments-direct"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ConfirmPaymentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: str = Field(pattern=r"^(cash|pix|not_received)$")
    amount_cents: int | None = Field(default=None, ge=0)


class ConfirmPaymentOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_id: int
    outcome: str
    dispute_opened: bool


@router.post("/{delivery_id}/payment-confirmation", response_model=ConfirmPaymentOut)
async def confirm_payment(
    delivery_id: int,
    body: ConfirmPaymentIn,
    scope: CourierScopeDep,
    session: SessionDep,
) -> ConfirmPaymentOut:
    """Confirm direct payment for a delivery (RN-026). 'não recebi' → opens dispute."""
    delivery = await get_delivery_for_courier(
        session, delivery_id=delivery_id, courier_id=scope.courier_id
    )
    _, dispute = await confirm_direct_payment(
        session,
        delivery=delivery,
        courier_id=scope.courier_id,
        outcome=body.outcome,
        amount_cents=body.amount_cents,
    )
    await session.commit()
    return ConfirmPaymentOut(
        delivery_id=delivery.id,
        outcome=body.outcome,
        dispute_opened=dispute is not None,
    )


class ReceiptOut(BaseModel):
    """Recibo do pagamento direto (tela 08). Transparência sem PII além do permitido (RN-013)."""

    model_config = ConfigDict(extra="forbid")
    delivery_id: int
    public_token: str
    reference_number: str | None
    amount_cents: int | None
    outcome: str
    status: str
    confirmed_at: datetime | None


@router.get("/{delivery_id}/receipt", response_model=ReceiptOut)
async def get_receipt(
    delivery_id: int,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> ReceiptOut:
    """The store's receipt for a direct-paid delivery (tela 08). Area+merchant scoped (404)."""
    delivery = await get_delivery(
        session,
        area_id=scope.area_id,
        merchant_id=scope.merchant_id,
        delivery_id=delivery_id,
    )
    confirmation = await get_confirmation_for_delivery(
        session, area_id=scope.area_id, delivery_id=delivery.id
    )
    return ReceiptOut(
        delivery_id=delivery.id,
        public_token=delivery.public_token,
        reference_number=delivery.reference_number,
        amount_cents=confirmation.amount_cents if confirmation else None,
        outcome=confirmation.outcome if confirmation else "pending",
        status=delivery.state,
        confirmed_at=confirmation.created_at if confirmation else None,
    )


__all__ = ["router"]
