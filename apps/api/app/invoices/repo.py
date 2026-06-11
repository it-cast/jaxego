"""Invoice persistence — idempotent close, billable-delivery aggregation queries.

`get_invoice_for_competence` loads the (merchant, competence) invoice — the UNIQUE
constraint backs the 1/loja/competência idempotency (D-01). `billable_deliveries`
returns the DIRECT deliveries with a recorded platform fee in the month (the invoice
lines are DERIVED from these — TH-03, never user input). Queries use the declared
indexes (no N+1).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery
from app.invoices.models import InvoiceLineItem, PlatformInvoice


async def get_invoice_for_competence(
    session: AsyncSession, *, area_id: int, merchant_id: int, competence: str
) -> PlatformInvoice | None:
    """Load the (merchant, competence) invoice or None (idempotency lookup — D-01)."""
    stmt = select(PlatformInvoice).where(
        PlatformInvoice.area_id == area_id,
        PlatformInvoice.merchant_id == merchant_id,
        PlatformInvoice.competence == competence,
    )
    return (await session.execute(stmt)).scalars().first()


async def get_invoice_for_area(
    session: AsyncSession, *, invoice_id: int, area_id: int
) -> PlatformInvoice | None:
    """Load an invoice scoped to an area (IDOR closed in the WHERE clause)."""
    stmt = select(PlatformInvoice).where(
        PlatformInvoice.id == invoice_id, PlatformInvoice.area_id == area_id
    )
    return (await session.execute(stmt)).scalars().first()


async def billable_deliveries(
    session: AsyncSession, *, area_id: int, merchant_id: int, since: datetime, until: datetime
) -> list[Delivery]:
    """Direct deliveries with a recorded platform fee created in [since, until).

    The platform fee on a direct delivery is RECORDED on `delivery.fee_cents` at
    creation (Phase 15) — the invoice lines are derived from these rows (TH-03). Single
    query, index-backed by (area_id, merchant_id).
    """
    stmt = select(Delivery).where(
        Delivery.area_id == area_id,
        Delivery.merchant_id == merchant_id,
        Delivery.payment_method == "direct",
        Delivery.fee_cents > 0,
        Delivery.created_at >= since,
        Delivery.created_at < until,
    )
    return list((await session.execute(stmt)).scalars().all())


async def merchant_ids_with_billables(
    session: AsyncSession, *, since: datetime, until: datetime
) -> list[tuple[int, int]]:
    """Distinct (area_id, merchant_id) pairs with billable direct deliveries in window."""
    stmt = (
        select(Delivery.area_id, Delivery.merchant_id)
        .where(
            Delivery.payment_method == "direct",
            Delivery.fee_cents > 0,
            Delivery.created_at >= since,
            Delivery.created_at < until,
        )
        .group_by(Delivery.area_id, Delivery.merchant_id)
    )
    return [(row.area_id, row.merchant_id) for row in (await session.execute(stmt)).all()]


async def line_items_for_invoice(
    session: AsyncSession, *, invoice_id: int
) -> list[InvoiceLineItem]:
    """All line items of an invoice (index-backed by invoice_id)."""
    stmt = select(InvoiceLineItem).where(InvoiceLineItem.invoice_id == invoice_id)
    return list((await session.execute(stmt)).scalars().all())
