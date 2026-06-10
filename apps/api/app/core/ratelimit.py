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
    """Too many requests from this client in the window (429)."""

    status_code = 429
    code = "rate_limited"

    def __init__(self) -> None:
        super().__init__("Muitas tentativas. Aguarde um momento e tente de novo.")


class SlidingWindowLimiter:
    """Allow at most `limit` hits per `window` per key (aware UTC)."""

    def __init__(self, *, limit: int, window: timedelta) -> None:
        self._limit = limit
        self._window = window
        self._hits: dict[str, deque[datetime]] = defaultdict(deque)

    def check(self, key: str, *, now: datetime | None = None) -> None:
        """Record a hit for `key`; raise RateLimitedError if over the limit."""
        current = now or datetime.now(UTC)
        cutoff = current - self._window
        bucket = self._hits[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._limit:
            raise RateLimitedError()
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
