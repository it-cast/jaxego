"""Structured JSON logging configuration (structlog) writing to stdout.

Every log line is JSON and carries the required fields from
`config.json > observability.required_log_fields` when bound via contextvars.
No PII is ever logged (see `pii_fields_forbidden_in_logs`).
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structlog + stdlib logging to emit JSON to stdout."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
