"""Platform invoice service (Phase 15 — REQ-037, RN-025 / D-01/D-02).

The monthly platform-fee invoice of the back-office direct modality. Money is integer
CENTS (DRV-009); datetimes aware UTC (TD-010). Values are PARAMETRISED (config/seed —
D-07), never hardcoded.

- `competence_for` / `close_invoice` — close ONE merchant's invoice for a competence,
  idempotent (UNIQUE(area,merchant,competence) → a re-run returns the existing one,
  D-01). Lines are DERIVED from the merchant's direct deliveries' recorded fee (TH-03,
  never user input). `amount_cents` is the exact integer SUM of the lines.
- `close_invoices_for_month` (cron, dia 1º) — close every merchant with billables in
  the previous month. Idempotent across the whole sweep.
- `mark_overdue` — flip open invoices past `due_at` to `overdue` (delinquency).
- `pay_invoice` — charge the open/overdue invoice via the `PaymentPort`; on success set
  `paid`. NEVER moves money without a confirmed charge (TH-07).
- `is_blocked_by_overdue_invoice` — the F-03 E5 guard predicate: an invoice overdue more
  than `invoice_overdue_block_days` blocks delivery creation (server-side — TH-08).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.db.mixins import ensure_aware_utc
from app.invoices import repo
from app.invoices.models import InvoiceLineItem, PlatformInvoice
from app.payments.port import Customer, PaymentPort, Split

logger = structlog.get_logger("invoices")


class InvoiceOverdueError(AppError):
    """A platform-fee invoice is overdue beyond the threshold — creation is blocked (F-03 E5)."""

    status_code = 402
    code = "invoice_overdue"

    def __init__(self) -> None:
        super().__init__(
            "Há uma fatura de plataforma vencida. Pague a fatura para voltar a criar entregas."
        )


class InvoiceNotPayableError(AppError):
    """The invoice is already paid (or otherwise not in a payable state)."""

    status_code = 409
    code = "invoice_not_payable"

    def __init__(self) -> None:
        super().__init__("Esta fatura não está em aberto.")


def competence_for(moment: datetime) -> str:
    """The YYYY-MM competence string of `moment` (aware-UTC)."""
    m = ensure_aware_utc(moment)
    return f"{m.year:04d}-{m.month:02d}"


def _previous_competence(now: datetime) -> tuple[str, datetime, datetime]:
    """(competence, since, until) for the month BEFORE `now` (dia 1º close)."""
    now = ensure_aware_utc(now)
    first_of_this_month = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    # `since` = first instant of the previous month; `until` = first of this month.
    until = first_of_this_month
    prev_last = first_of_this_month - timedelta(days=1)
    since = prev_last.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return competence_for(since), since, until


def _competence_window(competence: str) -> tuple[datetime, datetime]:
    """[since, until) for an explicit YYYY-MM competence (aware-UTC)."""
    year, month = (int(p) for p in competence.split("-"))
    since = datetime(year, month, 1, tzinfo=UTC)
    until = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=UTC)
    return since, until


async def close_invoice(
    session: AsyncSession,
    *,
    area_id: int,
    merchant_id: int,
    competence: str,
    now: datetime | None = None,
) -> PlatformInvoice:
    """Close one merchant's invoice for a competence (idempotent — D-01).

    A re-run returns the existing invoice unchanged (1/loja/competência). Lines are
    derived from the merchant's direct deliveries with a recorded fee in the month; the
    amount is their exact integer-cents sum (TH-03). `due_at` is parametrised (D-07).
    """
    now = ensure_aware_utc(now or datetime.now(UTC))
    existing = await repo.get_invoice_for_competence(
        session, area_id=area_id, merchant_id=merchant_id, competence=competence
    )
    if existing is not None:
        return existing

    since, until = _competence_window(competence)
    deliveries = await repo.billable_deliveries(
        session, area_id=area_id, merchant_id=merchant_id, since=since, until=until
    )
    total = sum(d.fee_cents for d in deliveries)
    due_at = now + timedelta(days=settings.invoice_due_days)
    invoice = PlatformInvoice(
        area_id=area_id,
        merchant_id=merchant_id,
        competence=competence,
        amount_cents=total,
        status="open",
        due_at=due_at,
        closed_at=now,
    )
    session.add(invoice)
    await session.flush()

    for d in deliveries:
        session.add(
            InvoiceLineItem(
                area_id=area_id,
                invoice_id=invoice.id,
                delivery_id=d.id,
                description=f"Taxa de plataforma — entrega #{d.id}",
                amount_cents=d.fee_cents,
            )
        )
    await session.flush()
    logger.info(
        "invoice.closed",
        area_id=area_id,
        merchant_id=merchant_id,
        competence=competence,
        amount_cents=total,
        lines=len(deliveries),
    )
    return invoice


async def close_invoices_for_month(
    session_factory: async_sessionmaker[AsyncSession], *, now: datetime | None = None
) -> int:
    """Cron (dia 1º): close the previous month's invoice for every merchant. Idempotent."""
    now = ensure_aware_utc(now or datetime.now(UTC))
    competence, since, until = _previous_competence(now)
    closed = 0
    async with session_factory() as session:
        pairs = await repo.merchant_ids_with_billables(session, since=since, until=until)
        for area_id, merchant_id in pairs:
            existing = await repo.get_invoice_for_competence(
                session, area_id=area_id, merchant_id=merchant_id, competence=competence
            )
            if existing is not None:
                continue
            await close_invoice(
                session,
                area_id=area_id,
                merchant_id=merchant_id,
                competence=competence,
                now=now,
            )
            closed += 1
        await session.commit()
    logger.info("invoice.close_month", competence=competence, closed=closed)
    return closed


async def mark_overdue(
    session_factory: async_sessionmaker[AsyncSession], *, now: datetime | None = None
) -> int:
    """Cron: flip OPEN invoices past their due date to OVERDUE. Idempotent."""
    now = ensure_aware_utc(now or datetime.now(UTC))
    changed = 0
    async with session_factory() as session:
        stmt = select(PlatformInvoice).where(PlatformInvoice.status == "open")
        for inv in (await session.execute(stmt)).scalars().all():
            if ensure_aware_utc(inv.due_at) < now:
                inv.status = "overdue"
                changed += 1
        await session.commit()
    logger.info("invoice.mark_overdue", changed=changed)
    return changed


async def pay_invoice(
    session: AsyncSession,
    *,
    invoice_id: int,
    area_id: int,
    payment: PaymentPort,
    customer_name: str = "Loja",
    customer_document: str = "",
    customer_email: str = "",
    now: datetime | None = None,
) -> PlatformInvoice:
    """Charge an open/overdue invoice via the PaymentPort; set paid on success (TH-07).

    Area-scoped (IDOR → 404). NEVER moves money without a confirmed charge: the status
    flips to `paid` only after the gateway returns a paid result.
    """
    now = ensure_aware_utc(now or datetime.now(UTC))
    invoice = await repo.get_invoice_for_area(session, invoice_id=invoice_id, area_id=area_id)
    if invoice is None:
        raise NotFoundError("Fatura não encontrada.")
    if invoice.status not in ("open", "overdue"):
        raise InvoiceNotPayableError()

    reference = f"inv_{invoice.id}_{invoice.competence}"
    customer = Customer(name=customer_name, document=customer_document, email=customer_email)
    # The whole invoice goes to the platform's own Safe2Pay recipient (single split leg —
    # the invariant amount == Σ splits holds). May raise PaymentGatewayError → the invoice
    # stays unpaid (TH-07 — never paid without a confirmed charge).
    jaxego_recipient = settings.safe2pay_jaxego_recipient or "jaxego"
    result = await payment.charge_with_split(
        amount_cents=invoice.amount_cents,
        splits=[Split(recipient=jaxego_recipient, amount_cents=invoice.amount_cents)],
        reference=reference,
        method="pix",
        customer=customer,
    )
    invoice.status = "paid"
    invoice.paid_at = now
    invoice.transaction_id = result.transaction_id
    await session.flush()
    logger.info("invoice.paid", area_id=area_id, invoice_id=invoice.id)
    return invoice


async def is_blocked_by_overdue_invoice(
    session: AsyncSession, *, area_id: int, merchant_id: int, now: datetime | None = None
) -> bool:
    """F-03 E5 predicate: an invoice overdue > `invoice_overdue_block_days` blocks creation.

    Server-side (TH-08): an `open`/`overdue` invoice whose due date is more than the
    parametrised threshold in the past blocks the store from creating deliveries.
    """
    now = ensure_aware_utc(now or datetime.now(UTC))
    cutoff = now - timedelta(days=settings.invoice_overdue_block_days)
    stmt = select(PlatformInvoice).where(
        PlatformInvoice.area_id == area_id,
        PlatformInvoice.merchant_id == merchant_id,
        PlatformInvoice.status.in_(("open", "overdue")),
        PlatformInvoice.due_at < cutoff,
    )
    return (await session.execute(stmt)).scalars().first() is not None
