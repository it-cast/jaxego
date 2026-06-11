"""Daily reconciliation: extrato × platform_charges, divergence >R$0,01 → alert.

TH-I: integer-cent exact comparison; a difference greater than 1 cent is alerted
(not auto-corrected).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_reconcile_no_divergence(payments_seed, payment_stub, session_factory) -> None:
    from app.payments import reconcile, repo

    async with session_factory() as s:
        await repo.record_charge(
            s,
            area_id=payments_seed.area_a_id,
            idempotency_key="rec_1",
            transaction_id="tx_rec_1",
            amount_cents=1200,
            method="card",
            kind="delivery",
            status="paid",
        )
        await s.commit()

    # Stub statement mirrors the charge exactly → zero divergence.
    payment_stub.statement_entries = [("tx_rec_1", 1200)]
    divergences = await reconcile.reconcile(
        session_factory,
        payment_stub,
        since=datetime.now(UTC) - timedelta(days=1),
        until=datetime.now(UTC) + timedelta(days=1),
    )
    assert divergences == []


@pytest.mark.asyncio
async def test_reconcile_detects_divergence(payments_seed, payment_stub, session_factory) -> None:
    from app.payments import reconcile, repo

    async with session_factory() as s:
        await repo.record_charge(
            s,
            area_id=payments_seed.area_a_id,
            idempotency_key="rec_2",
            transaction_id="tx_rec_2",
            amount_cents=1200,
            method="card",
            kind="delivery",
            status="paid",
        )
        await s.commit()

    # Statement says 1300 → 100c divergence (> 1c) → alerted.
    payment_stub.statement_entries = [("tx_rec_2", 1300)]
    divergences = await reconcile.reconcile(
        session_factory,
        payment_stub,
        since=datetime.now(UTC) - timedelta(days=1),
        until=datetime.now(UTC) + timedelta(days=1),
    )
    assert len(divergences) == 1
    assert divergences[0]["transaction_id"] == "tx_rec_2"
    assert divergences[0]["diff_cents"] == 100
