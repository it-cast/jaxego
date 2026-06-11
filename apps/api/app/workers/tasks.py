"""arq worker tasks.

Foundation phase ships a single minimal task: `healthcheck`. arq refuses to
boot a `WorkerSettings` with an empty `functions` list, so this keeps the worker
alive and gives ops a trivial, side-effect-free job to enqueue as a liveness
probe. Domain jobs are added here from Phase 2 onward.
"""

from __future__ import annotations

from typing import Any


async def healthcheck(ctx: dict[str, Any]) -> str:
    """No-op liveness task; returns "ok" so the worker has a registered job."""
    return "ok"


# ---------------------------------------------------------------------------
# Phase 10 — recurring billing crons (idempotent; aware-UTC). Each resolves the
# session factory + PaymentPort from the worker ctx (D-09: real adapter in prod,
# Stub in dev/test). A failure inside one row never derails the sweep.
# ---------------------------------------------------------------------------
async def charge_subscriptions_daily(ctx: dict[str, Any]) -> int:
    """Charge active card subscriptions due today (SAAS-BILLING §7). Returns count."""
    from app.payments import subscriptions
    from app.payments.factory import get_payment_adapter

    return await subscriptions.charge_due_subscriptions(
        ctx["session_factory"], get_payment_adapter()
    )


async def sync_delinquency(ctx: dict[str, Any]) -> int:
    """Transition subscriptions by overdue days (>10d blocked, >20d cancelado)."""
    from app.payments import subscriptions

    return await subscriptions.sync_delinquency(ctx["session_factory"])


async def release_escrow(ctx: dict[str, Any]) -> int:
    """Release escrow holds FINALIZADA+24h without dispute (RN-006). Returns count."""
    from app.payments import escrow

    return await escrow.release_ready(ctx["session_factory"])


async def reconcile_safe2pay(ctx: dict[str, Any]) -> int:
    """Daily reconciliation: extrato × platform_charges; alert >R$0,01 (D-08)."""
    from datetime import UTC, datetime, timedelta

    from app.payments import reconcile
    from app.payments.factory import get_payment_adapter

    now = datetime.now(UTC)
    divergences = await reconcile.reconcile(
        ctx["session_factory"],
        get_payment_adapter(),
        since=now - timedelta(days=1),
        until=now,
    )
    return len(divergences)


async def process_safe2pay_event(
    ctx: dict[str, Any], transaction_id: str, event_status: str
) -> str:
    """Process a deduped Safe2Pay webhook event (heavy work off the request path).

    NEVER releases money on the webhook alone (TH-E): for an approved status it marks the
    matching charge paid (the escrow release stays with the 24h cron). A business error is
    swallowed (logged) — the event was already deduped, and re-processing must not loop.
    A real impl confirms via `GET Transaction/{id}` before any financial effect; with the
    Stub there is no network, so we trust the deduped status.
    """
    import structlog

    from app.payments import repo

    logger = structlog.get_logger("workers.payments")
    session_factory = ctx["session_factory"]
    approved = event_status in {"3", "4", "APROVADA", "ATIVA", "CONCLUIDA", "PAGO"}
    async with session_factory() as session:
        charge = await repo.get_charge_by_transaction(session, transaction_id=transaction_id)
        if charge is not None and approved and charge.status == "open":
            charge.status = "paid"
        await session.commit()
    logger.info("payments.process_event", transaction_id=transaction_id, approved=approved)
    return "ok"
