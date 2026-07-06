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


async def charge_pix_subscriptions_daily(ctx: dict[str, Any]) -> int:
    """Schedule PIX Automático chargeSchedules for approved subscriptions due today."""
    from app.payments import subscriptions
    from app.payments.factory import get_payment_adapter

    return await subscriptions.charge_due_pix_subscriptions(
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


# ---------------------------------------------------------------------------
# Phase 15 — back-office financial crons (idempotent; aware-UTC). Each resolves the
# session factory (+ PaymentPort where money moves) from the worker ctx.
# ---------------------------------------------------------------------------
async def close_platform_invoices(ctx: dict[str, Any]) -> int:
    """Cron (dia 1º): close last month's platform-fee invoice per merchant (REQ-037)."""
    from app.invoices import service

    return await service.close_invoices_for_month(ctx["session_factory"])


async def mark_invoices_overdue(ctx: dict[str, Any]) -> int:
    """Cron: flip OPEN platform invoices past their due date to OVERDUE (F-03 E5)."""
    from app.invoices import service

    return await service.mark_overdue(ctx["session_factory"])


async def expire_dispute_blocks(ctx: dict[str, Any]) -> int:
    """Cron: expire dispute blocks past their 90-day window (RN-027). Idempotent."""
    from app.payments_direct import disputes

    return await disputes.expire_blocks(ctx["session_factory"])


async def reconcile_finance_daily(ctx: dict[str, Any]) -> int:
    """Cron: daily back-office reconciliation (charges/payouts/refunds × extrato — D-05)."""
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

    Handles two event families:
    1. PIX Automático authorization APROVADA — activates the subscription.
    2. Charge paid (card or PIX QR) — marks the charge paid; activates PIX one-time subs.

    NEVER releases money on the webhook alone (TH-E). Business errors are swallowed
    (logged) — the event was already deduped, and re-processing must not loop.
    """
    import structlog

    from app.payments import repo, subscriptions

    logger = structlog.get_logger("workers.payments")
    session_factory = ctx["session_factory"]
    approved = event_status in {"3", "4", "APROVADA", "ATIVA", "CONCLUIDA", "PAGO"}

    async with session_factory() as session:
        # 1. PIX Automático authorization APROVADA: look up by authorization id.
        if event_status == "APROVADA":
            found = await subscriptions.activate_approved_pix(
                session, pix_autorizacao_id=transaction_id
            )
            if found:
                await session.commit()
                logger.info("payments.pix_auto_approved", authorization_id=transaction_id)
                return "ok"

        # 2. Standard charge event (card or PIX QR).
        charge = await repo.get_charge_by_transaction(session, transaction_id=transaction_id)
        if charge is not None and approved and charge.status == "open":
            charge.status = "paid"
            # PIX one-time subscription: activate on first charge confirmed paid.
            if charge.subscription_id is not None and charge.method == "pix":
                await subscriptions.activate_pix_on_charge_paid(
                    session, subscription_id=charge.subscription_id
                )
        await session.commit()

    logger.info("payments.process_event", transaction_id=transaction_id, approved=approved)
    return "ok"
