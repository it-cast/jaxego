"""Daily back-office reconciliation including repasses (Phase 15 — D-05).

The daily reconciliation now also cross-checks paid courier repasses (withdrawals)
against the extrato. Covers: a payout matching the extrato → clean; a payout whose
extrato amount diverges → alerted; a payout absent from the extrato (money our ledger
says moved but the PSP does not show) → alerted.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.withdrawals.models import Withdrawal


async def _paid_withdrawal(
    s, *, area_id: int, courier_id: int, reference: str, tx: str, amount: int
) -> None:
    s.add(
        Withdrawal(
            area_id=area_id,
            courier_id=courier_id,
            reference=reference,
            amount_cents=amount,
            status="paid",
            transaction_id=tx,
            settled_at=datetime.now(UTC),
        )
    )
    await s.flush()


@pytest.mark.asyncio
async def test_reconcile_payout_matches(payments_seed, payment_stub, session_factory) -> None:
    from app.payments import reconcile

    async with session_factory() as s:
        await _paid_withdrawal(
            s,
            area_id=payments_seed.area_a_id,
            courier_id=payments_seed.courier_id,
            reference="wd_rec_ok",
            tx="tx_payout_ok",
            amount=2000,
        )
        await s.commit()

    payment_stub.statement_entries = [("tx_payout_ok", 2000)]
    divergences = await reconcile.reconcile(
        session_factory,
        payment_stub,
        since=datetime.now(UTC) - timedelta(days=1),
        until=datetime.now(UTC) + timedelta(days=1),
    )
    assert divergences == []


@pytest.mark.asyncio
async def test_reconcile_payout_amount_diverges(
    payments_seed, payment_stub, session_factory
) -> None:
    from app.payments import reconcile

    async with session_factory() as s:
        await _paid_withdrawal(
            s,
            area_id=payments_seed.area_a_id,
            courier_id=payments_seed.courier_id,
            reference="wd_rec_diff",
            tx="tx_payout_diff",
            amount=2000,
        )
        await s.commit()

    # Extrato says 1800 for the payout → 200c divergence (> 1c) → alerted.
    payment_stub.statement_entries = [("tx_payout_diff", 1800)]
    divergences = await reconcile.reconcile(
        session_factory,
        payment_stub,
        since=datetime.now(UTC) - timedelta(days=1),
        until=datetime.now(UTC) + timedelta(days=1),
    )
    assert len(divergences) == 1
    assert divergences[0]["transaction_id"] == "tx_payout_diff"
    assert divergences[0]["diff_cents"] == 200


@pytest.mark.asyncio
async def test_reconcile_payout_missing_from_extrato(
    payments_seed, payment_stub, session_factory
) -> None:
    from app.payments import reconcile

    async with session_factory() as s:
        await _paid_withdrawal(
            s,
            area_id=payments_seed.area_a_id,
            courier_id=payments_seed.courier_id,
            reference="wd_rec_missing",
            tx="tx_payout_missing",
            amount=2000,
        )
        await s.commit()

    # Our ledger says the repasse happened; the extrato is empty → divergence.
    payment_stub.statement_entries = []
    divergences = await reconcile.reconcile(
        session_factory,
        payment_stub,
        since=datetime.now(UTC) - timedelta(days=1),
        until=datetime.now(UTC) + timedelta(days=1),
    )
    assert len(divergences) == 1
    assert divergences[0]["transaction_id"] == "tx_payout_missing"
    assert divergences[0]["statement_cents"] is None
