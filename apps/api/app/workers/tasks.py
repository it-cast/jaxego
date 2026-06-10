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
