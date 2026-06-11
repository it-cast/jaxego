"""F-03 E5 overdue-invoice guard (Phase 15 — D-02 / TH-08).

An invoice overdue MORE than the parametrised threshold (>7d) blocks delivery creation
server-side; overdue 5 days still allows it. The predicate is exercised directly and via
the create_delivery guard (raising InvoiceOverdueError, 402).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


def _overdue_invoice(*, area_id: int, merchant_id: int, due_days_ago: int):
    from app.invoices.models import PlatformInvoice

    now = datetime.now(UTC)
    return PlatformInvoice(
        area_id=area_id,
        merchant_id=merchant_id,
        competence="2026-05",
        amount_cents=600,
        status="overdue",
        due_at=now - timedelta(days=due_days_ago),
        closed_at=now - timedelta(days=due_days_ago + 7),
    )


@pytest.mark.asyncio
async def test_overdue_more_than_7_days_blocks(invoice_seed, session_factory) -> None:
    from app.invoices.service import is_blocked_by_overdue_invoice

    async with session_factory() as s:
        s.add(
            _overdue_invoice(
                area_id=invoice_seed.area_id, merchant_id=invoice_seed.merchant_id, due_days_ago=8
            )
        )
        await s.commit()

    async with session_factory() as s:
        blocked = await is_blocked_by_overdue_invoice(
            s, area_id=invoice_seed.area_id, merchant_id=invoice_seed.merchant_id
        )
        assert blocked is True


@pytest.mark.asyncio
async def test_overdue_5_days_allows(invoice_seed, session_factory) -> None:
    from app.invoices.service import is_blocked_by_overdue_invoice

    async with session_factory() as s:
        s.add(
            _overdue_invoice(
                area_id=invoice_seed.area_id, merchant_id=invoice_seed.merchant_id, due_days_ago=5
            )
        )
        await s.commit()

    async with session_factory() as s:
        blocked = await is_blocked_by_overdue_invoice(
            s, area_id=invoice_seed.area_id, merchant_id=invoice_seed.merchant_id
        )
        assert blocked is False


@pytest.mark.asyncio
async def test_no_invoice_allows(invoice_seed, session_factory) -> None:
    from app.invoices.service import is_blocked_by_overdue_invoice

    async with session_factory() as s:
        blocked = await is_blocked_by_overdue_invoice(
            s, area_id=invoice_seed.area_id, merchant_id=invoice_seed.merchant_id
        )
        assert blocked is False


@pytest.mark.asyncio
async def test_mark_overdue_flips_open_past_due(invoice_seed, session_factory) -> None:
    from app.invoices import service
    from app.invoices.models import PlatformInvoice

    now = datetime.now(UTC)
    async with session_factory() as s:
        s.add(
            PlatformInvoice(
                area_id=invoice_seed.area_id,
                merchant_id=invoice_seed.merchant_id,
                competence="2026-05",
                amount_cents=600,
                status="open",
                due_at=now - timedelta(days=1),
                closed_at=now - timedelta(days=8),
            )
        )
        await s.commit()

    changed = await service.mark_overdue(session_factory, now=now)
    assert changed == 1

    async with session_factory() as s:
        from sqlalchemy import select

        inv = (await s.execute(select(PlatformInvoice))).scalars().one()
        assert inv.status == "overdue"
