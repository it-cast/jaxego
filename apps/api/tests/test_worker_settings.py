"""Regression tests for the arq WorkerSettings (post-smoke fix).

The live smoke (docker compose up) caught the worker in a crash loop:
arq raises "at least one function or cron_job must be registered" when
`WorkerSettings.functions` is empty. These tests guard against that regression
so gate 7 (tests) fails before such a worker ever ships again.
"""

from __future__ import annotations

import inspect

from app.workers.settings import WorkerSettings
from app.workers.tasks import healthcheck


def test_worker_has_at_least_one_function() -> None:
    """arq refuses to boot with an empty functions list; ensure >=1 is registered."""
    functions = getattr(WorkerSettings, "functions", [])
    cron_jobs = getattr(WorkerSettings, "cron_jobs", [])
    assert len(functions) + len(cron_jobs) >= 1, (
        "WorkerSettings must register at least one function or cron_job, "
        "otherwise arq crash-loops on boot"
    )


def test_registered_functions_are_callable() -> None:
    """Every registered function must actually be callable (arq invokes them)."""
    for fn in WorkerSettings.functions:
        assert callable(fn), f"registered worker function is not callable: {fn!r}"


def test_healthcheck_is_async() -> None:
    """The heartbeat task is an async coroutine function (arq requirement)."""
    assert inspect.iscoroutinefunction(healthcheck)
