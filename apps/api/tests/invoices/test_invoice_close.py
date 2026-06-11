"""Platform invoice closing + payment (Phase 15 — REQ-037 / D-01/D-02).

The dia-1º job aggregates the platform fee RECORDED on the store's direct deliveries of
a competence into ONE invoice (1/loja/competência — idempotent). Money is integer cents,
derived from the deliveries (TH-03 — never user input). Paying goes through the
PaymentStub (no network).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.invoices.conftest import make_direct_delivery


@pytest.mark.asyncio
async def test_close_sums_direct_fees_into_one_invoice(invoice_seed, session_factory) -> None:
    from app.invoices import service
    from app.invoices.models import PlatformInvoice

    may = datetime(2026, 5, 10, 12, 0, tzinfo=UTC)
    async with session_factory() as s:
        for _ in range(3):
            await make_direct_delivery(
                s,
                area_id=invoice_seed.area_id,
                merchant_id=invoice_seed.merchant_id,
                dropoff_nbhd_id=invoice_seed.dropoff_nbhd_id,
                fee_cents=200,
                created_at=may,
            )
        await s.commit()

    async with session_factory() as s:
        invoice = await service.close_invoice(
            s,
            area_id=invoice_seed.area_id,
            merchant_id=invoice_seed.merchant_id,
            competence="2026-05",
            now=datetime(2026, 6, 1, 2, 0, tzinfo=UTC),
        )
        await s.commit()
        assert invoice.amount_cents == 600  # 3 × 200, exact integer cents
        assert invoice.status == "open"

    async with session_factory() as s:
        from sqlalchemy import select

        rows = (await s.execute(select(PlatformInvoice))).scalars().all()
        assert len(rows) == 1


@pytest.mark.asyncio
async def test_close_is_idempotent_one_per_competence(invoice_seed, session_factory) -> None:
    from app.invoices import service
    from app.invoices.models import PlatformInvoice

    may = datetime(2026, 5, 10, 12, 0, tzinfo=UTC)
    async with session_factory() as s:
        await make_direct_delivery(
            s,
            area_id=invoice_seed.area_id,
            merchant_id=invoice_seed.merchant_id,
            dropoff_nbhd_id=invoice_seed.dropoff_nbhd_id,
            fee_cents=200,
            created_at=may,
        )
        await s.commit()

    async with session_factory() as s:
        a = await service.close_invoice(
            s,
            area_id=invoice_seed.area_id,
            merchant_id=invoice_seed.merchant_id,
            competence="2026-05",
        )
        await s.commit()
        first_id = a.id

    async with session_factory() as s:
        b = await service.close_invoice(
            s,
            area_id=invoice_seed.area_id,
            merchant_id=invoice_seed.merchant_id,
            competence="2026-05",
        )
        await s.commit()
        assert b.id == first_id  # same row, no duplicate

    async with session_factory() as s:
        from sqlalchemy import select

        assert len((await s.execute(select(PlatformInvoice))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_pay_invoice_via_port(invoice_seed, session_factory, payment_stub) -> None:
    from app.invoices import service

    may = datetime(2026, 5, 10, 12, 0, tzinfo=UTC)
    async with session_factory() as s:
        await make_direct_delivery(
            s,
            area_id=invoice_seed.area_id,
            merchant_id=invoice_seed.merchant_id,
            dropoff_nbhd_id=invoice_seed.dropoff_nbhd_id,
            fee_cents=500,
            created_at=may,
        )
        await s.commit()

    async with session_factory() as s:
        invoice = await service.close_invoice(
            s,
            area_id=invoice_seed.area_id,
            merchant_id=invoice_seed.merchant_id,
            competence="2026-05",
        )
        await s.commit()
        invoice_id = invoice.id

    async with session_factory() as s:
        paid = await service.pay_invoice(
            s, invoice_id=invoice_id, area_id=invoice_seed.area_id, payment=payment_stub
        )
        await s.commit()
        assert paid.status == "paid"
        assert paid.transaction_id is not None
        assert paid.paid_at is not None
