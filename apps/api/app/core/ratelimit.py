"""In-process sliding-window rate limiter (TH-07, owasp A04).

A minimal, dependency-free limiter for expensive endpoints (signup calls Receita
+ SMS). Keyed by client IP. This is a single-process guard suitable for the
pilot; a distributed limiter (Redis) is a documented future upgrade
(TD — post_launch). All datetimes are aware UTC (TD-010).
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import Request

from app.core.exceptions import AppError


class RateLimitedError(AppError):
    """Too many requests from this client in the window (429).

    `retry_after` (seconds), when given, is surfaced as the standard `Retry-After`
    response header (RFC 7807 + header — D-05 / TH-08) by the global error handler.
    """

    status_code = 429
    code = "rate_limited"

    def __init__(self, *, retry_after: int | None = None) -> None:
        super().__init__("Muitas tentativas. Aguarde um momento e tente de novo.")
        if retry_after is not None:
            self.headers["Retry-After"] = str(retry_after)


class SlidingWindowLimiter:
    """Allow at most `limit` hits per `window` per key (aware UTC)."""

    def __init__(self, *, limit: int, window: timedelta) -> None:
        self._limit = limit
        self._window = window
        self._hits: dict[str, deque[datetime]] = defaultdict(deque)

    def check(
        self, key: str, *, now: datetime | None = None, retry_after: int | None = None
    ) -> None:
        """Record a hit for `key`; raise RateLimitedError if over the limit.

        `retry_after` (seconds), when given, is attached to the 429 as the
        `Retry-After` header (D-05 / TH-08).
        """
        current = now or datetime.now(UTC)
        cutoff = current - self._window
        bucket = self._hits[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._limit:
            raise RateLimitedError(retry_after=retry_after)
        bucket.append(current)

    def reset(self) -> None:
        """Clear all state (used by tests)."""
        self._hits.clear()


# Signup: 5/min per IP — derived in RESEARCH (expensive: Receita + SMS) (TH-07).
signup_limiter = SlidingWindowLimiter(limit=5, window=timedelta(minutes=1))


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def signup_rate_limit(request: Request) -> None:
    """FastAPI dependency: enforce the signup rate limit by client IP."""
    signup_limiter.check(_client_ip(request))
