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
