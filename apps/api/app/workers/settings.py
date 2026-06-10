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

from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.tasks import healthcheck


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    # At least one job must be registered or arq refuses to boot.
    # Domain jobs are appended here from Phase 2 onward.
    functions = [healthcheck]
