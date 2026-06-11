"""arq worker settings — skeleton.

Defines the arq `WorkerSettings` pointing at Redis (read from env). The
foundation phase registers a single minimal `healthcheck` task: arq refuses to
boot with an empty `functions` list ("at least one function or cron_job must be
registered"), so this keeps the worker out of a crash loop. Domain jobs are
added from Phase 2 onward.

Run with:
    uv run arq app.workers.settings.WorkerSettings
"""

from __future__ import annotations

from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.session import async_session_factory
from app.notifications.tasks import notify_task
from app.workers.appeals import enforce_appeal_sla
from app.workers.dispatch import dispatch_offer_task, send_push_task
from app.workers.document_expiry import (
    escalate_stale_reviews_task,
    expire_documents_task,
)
from app.workers.document_reprocess import reprocess_document_task
from app.workers.lifecycle import (
    absent_timeout,
    anonymize_inactive,
    delete_ephemeral,
    finalize_deliveries,
    purge_locations,
)
from app.workers.revalidate import revalidate_receita
from app.workers.scores import snapshot_scores
from app.workers.tasks import (
    charge_subscriptions_daily,
    close_platform_invoices,
    expire_dispute_blocks,
    healthcheck,
    mark_invoices_overdue,
    process_safe2pay_event,
    reconcile_finance_daily,
    reconcile_safe2pay,
    release_escrow,
    sync_delinquency,
)
from app.workers.webhooks import deliver_due_webhooks, purge_idempotency_keys


async def _on_startup(ctx: dict[str, Any]) -> None:
    """Expose the async session factory to jobs (revalidate_receita uses it)."""
    ctx["session_factory"] = async_session_factory


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = _on_startup

    # At least one job must be registered or arq refuses to boot.
    # Phase 4: revalidate_receita (E4 retry 6/6/12/24h).
    # Phase 5: document reprocess (post-upload) + expiry + 48h escalation (E5).
    functions = [
        healthcheck,
        revalidate_receita,
        reprocess_document_task,
        expire_documents_task,
        escalate_stale_reviews_task,
        # Phase 8: cascade orchestration + Web Push send (LOW-1 / D-08).
        dispatch_offer_task,
        send_push_task,
        # Phase 9: multichannel recipient notifications (RN-018 / RN-031).
        notify_task,
        # Phase 10: recurring billing + escrow + reconciliation crons (idempotent).
        charge_subscriptions_daily,
        sync_delinquency,
        release_escrow,
        reconcile_safe2pay,
        # Phase 10: webhook event processing (enqueued from the public webhook endpoint).
        process_safe2pay_event,
        # Phase 12: public-API idempotency purge + outbound webhook delivery.
        purge_idempotency_keys,
        deliver_due_webhooks,
        # Phase 13: daily score snapshot (idempotent, no financial effect — ADR-013).
        snapshot_scores,
        # Phase 13: appeal SLA enforcement (auto-revert + alert, idempotent — LOW-1).
        enforce_appeal_sla,
        # Phase 15: back-office financial crons (fatura/bloqueio/conciliação — idempotent).
        close_platform_invoices,
        mark_invoices_overdue,
        expire_dispute_blocks,
        reconcile_finance_daily,
    ]

    # Phase 9 cron jobs (idempotent; failure does not derail the worker).
    cron_jobs = [
        # FINALIZADA 24h after ENTREGUE with no open dispute (D-06) — every 5 min.
        cron(finalize_deliveries, minute=set(range(0, 60, 5))),
        # Purge delivery_locations of terminal deliveries >24h (LGPD) — hourly.
        cron(purge_locations, minute={7}),
        # "ausente" >10min → enable return (D-07 E2) — every minute.
        cron(absent_timeout, minute=set(range(0, 60))),
        # Phase 10 — recurring billing crons (aware-UTC, idempotent).
        # Charge due card subscriptions daily at 06:00 UTC (SAAS-BILLING §7).
        cron(charge_subscriptions_daily, hour={6}, minute={0}),
        # Sync delinquency (10/20d) daily at 06:10 UTC.
        cron(sync_delinquency, hour={6}, minute={10}),
        # Release escrow FINALIZADA+24h without dispute — every 10 min (RN-006).
        cron(release_escrow, minute=set(range(0, 60, 10))),
        # Reconcile extrato × platform_charges daily at 07:00 UTC (D-08).
        cron(reconcile_safe2pay, hour={7}, minute={0}),
        # Phase 12 — purge expired idempotency snapshots hourly (T-05, LGPD/cleanup).
        cron(purge_idempotency_keys, minute={23}),
        # Phase 12 — sweep due webhook deliveries every minute (drives the 8× backoff).
        cron(deliver_due_webhooks, minute=set(range(0, 60))),
        # Phase 13 — daily score snapshot at 05:00 UTC (1/dia/courier, idempotent).
        cron(snapshot_scores, hour={5}, minute={0}),
        # Phase 13 — enforce appeal SLA every 5 min (auto-revert past-due undecided).
        cron(enforce_appeal_sla, minute=set(range(0, 60, 5))),
        # Phase 14 — LGPD jobs (REQ-048). Anonymise inactive (12m) daily at 03:30 UTC;
        # hard-delete ephemeral (30d) daily at 03:50 UTC. Idempotent, audited (D-01/D-02).
        cron(anonymize_inactive, hour={3}, minute={30}),
        cron(delete_ephemeral, hour={3}, minute={50}),
        # Phase 15 — close last month's platform-fee invoices on the 1st at 02:00 UTC
        # (REQ-037, idempotent — 1/loja/competência).
        cron(close_platform_invoices, day={1}, hour={2}, minute={0}),
        # Flip invoices past their due date to OVERDUE daily at 02:30 UTC (F-03 E5).
        cron(mark_invoices_overdue, hour={2}, minute={30}),
        # Expire 90-day dispute blocks daily at 02:40 UTC (RN-027, idempotent).
        cron(expire_dispute_blocks, hour={2}, minute={40}),
        # Daily back-office reconciliation at 07:30 UTC (D-05, divergence → alert).
        cron(reconcile_finance_daily, hour={7}, minute={30}),
    ]
