"""Daily reconciliation: Safe2Pay extrato × ledger (Phase 10 — D-08 / Phase 15 — D-05).

The cron compares the Safe2Pay statement (`PaymentPort.get_statement`) against our local
ledger in the window: paid `platform_charges` (Phase 10) AND, from Phase 15, paid
courier `withdrawals` (repasses) — both keyed by their Safe2Pay transaction id. A
difference greater than R$0,01 (1 cent) on a matched transaction, OR a record present on
only one side, is a DIVERGENCE → alerted to the platform admin (ERROR log; never
auto-corrected — TH-I). Comparison is in integer cents, exact.

The window is aware-UTC (TD-010). No N+1: the charges and withdrawals each load in a
single query and the statement is a single PSP call; matching is an in-memory dict join.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.payments import repo
from app.payments.port import PaymentPort

logger = structlog.get_logger("payments.reconcile")

# R$0,01 tolerance (TH-I) — any larger diff is alerted.
TOLERANCE_CENTS = 1


async def reconcile(
    session_factory: async_sessionmaker[AsyncSession],
    payment: PaymentPort,
    *,
    since: datetime,
    until: datetime,
) -> list[dict[str, Any]]:
    """Compare extrato × platform_charges in [since, until]; return the divergences.

    Each divergence dict carries `transaction_id`, `charge_cents`, `statement_cents`,
    `diff_cents`. Divergences >R$0,01 are logged ERROR (alert); the function never mutates
    a charge (TH-I — no auto-correct).
    """
    statement = await payment.get_statement(since=since, until=until)
    statement_by_tx = {e.transaction_id: e.amount_cents for e in statement}

    async with session_factory() as session:
        charges = await repo.list_charges_between(session, since=since, until=until)
        # Phase 15 (D-05): paid courier repasses (withdrawals) also appear on the extrato.
        from app.withdrawals import reconcile_repo

        payouts = await reconcile_repo.paid_withdrawals_between(
            session, since=since, until=until
        )

    # The local ledger side keyed by Safe2Pay transaction id (charges + payouts).
    local_by_tx: dict[str, int] = {}
    for charge in charges:
        if charge.transaction_id is not None:
            local_by_tx[charge.transaction_id] = charge.amount_cents
    for payout in payouts:
        if payout.transaction_id is not None:
            local_by_tx[payout.transaction_id] = payout.amount_cents

    divergences: list[dict[str, Any]] = []
    charge_txs: set[str] = set()
    for tx, charge_amount in local_by_tx.items():
        charge_txs.add(tx)
        statement_cents = statement_by_tx.get(tx)
        if statement_cents is None:
            divergences.append(
                {
                    "transaction_id": tx,
                    "charge_cents": charge_amount,
                    "statement_cents": None,
                    "diff_cents": charge_amount,
                }
            )
            continue
        diff = abs(charge_amount - statement_cents)
        if diff > TOLERANCE_CENTS:
            divergences.append(
                {
                    "transaction_id": tx,
                    "charge_cents": charge_amount,
                    "statement_cents": statement_cents,
                    "diff_cents": diff,
                }
            )

    # Statement entries with no matching charge (money moved without our record).
    for tx, amount in statement_by_tx.items():
        if tx not in charge_txs:
            divergences.append(
                {
                    "transaction_id": tx,
                    "charge_cents": None,
                    "statement_cents": amount,
                    "diff_cents": amount,
                }
            )

    if divergences:
        # Alert the platform admin (ERROR); no PII, no auto-correction (TH-I).
        logger.error("reconcile.divergence", count=len(divergences))
    else:
        logger.info("reconcile.clean")
    return divergences


async def reconcile_safe2pay(ctx: dict[str, Any]) -> int:
    """arq cron entrypoint. Returns the divergence count (also in tasks.py wrapper)."""
    from datetime import UTC, timedelta

    from app.payments.factory import get_payment_adapter

    now = datetime.now(UTC)
    divergences = await reconcile(
        ctx["session_factory"],
        get_payment_adapter(),
        since=now - timedelta(days=1),
        until=now,
    )
    return len(divergences)
