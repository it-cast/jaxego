"""/v1/invoices — store invoice listing + payment (Phase 15 — REQ-037, tela 15).

All routes are scoped to the authenticated store via `merchant_scope` (A01 / TH-03 —
IDOR closed in the WHERE clause). The amount is server-derived (TH-03); paying goes
through the `PaymentPort` (Stub in dev/test — D-09), never moving money without a
confirmed charge (TH-07).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.deliveries.dependencies import MerchantScopeDep
from app.invoices import service
from app.invoices.models import PlatformInvoice
from app.payments.factory import get_payment_adapter

router = APIRouter(prefix="/invoices", tags=["invoices"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class InvoiceRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    competence: str
    amount_cents: int
    status: str
    due_at: datetime
    paid_at: datetime | None


def _row(inv: PlatformInvoice) -> InvoiceRow:
    return InvoiceRow(
        id=inv.id,
        competence=inv.competence,
        amount_cents=inv.amount_cents,
        status=inv.status,
        due_at=inv.due_at,
        paid_at=inv.paid_at,
    )


@router.get("", response_model=list[InvoiceRow])
async def list_invoices(scope: MerchantScopeDep, session: SessionDep) -> list[InvoiceRow]:
    """List the store's platform-fee invoices (scoped to the store — TH-03)."""
    stmt = (
        select(PlatformInvoice)
        .where(
            PlatformInvoice.area_id == scope.area_id,
            PlatformInvoice.merchant_id == scope.merchant_id,
        )
        .order_by(PlatformInvoice.competence.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [_row(r) for r in rows]


@router.post("/{invoice_id}/pay", response_model=InvoiceRow)
async def pay_invoice(
    invoice_id: int, scope: MerchantScopeDep, session: SessionDep
) -> InvoiceRow:
    """Pay an open/overdue invoice via the PaymentPort (TH-07). Area-scoped (IDOR → 404)."""
    invoice = await service.pay_invoice(
        session,
        invoice_id=invoice_id,
        area_id=scope.area_id,
        payment=get_payment_adapter(),
    )
    await session.commit()
    return _row(invoice)


__all__ = ["router"]
