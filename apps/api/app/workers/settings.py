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
from app.workers.dispatch import dispatch_offer_task, send_push_task
from app.workers.document_expiry import (
    escalate_stale_reviews_task,
    expire_documents_task,
)
from app.workers.document_reprocess import reprocess_document_task
from app.workers.lifecycle import (
    absent_timeout,
    finalize_deliveries,
    purge_locations,
)
from app.workers.revalidate import revalidate_receita
from app.workers.tasks import healthcheck


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
    ]

    # Phase 9 cron jobs (idempotent; failure does not derail the worker).
    cron_jobs = [
        # FINALIZADA 24h after ENTREGUE with no open dispute (D-06) — every 5 min.
        cron(finalize_deliveries, minute=set(range(0, 60, 5))),
        # Purge delivery_locations of terminal deliveries >24h (LGPD) — hourly.
        cron(purge_locations, minute={7}),
        # "ausente" >10min → enable return (D-07 E2) — every minute.
        cron(absent_timeout, minute=set(range(0, 60))),
    ]
