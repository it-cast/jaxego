"""arq worker settings — skeleton.

Defines the arq `WorkerSettings` pointing at Redis (read from env). No domain
job exists in the foundation phase; the function list is an empty placeholder
that downstream phases extend.

Run with:
    uv run arq app.workers.settings.WorkerSettings
"""

from __future__ import annotations

from arq.connections import RedisSettings

from app.core.config import settings


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    # Domain jobs are registered here from Phase 2 onward.
    functions: list[object] = []
