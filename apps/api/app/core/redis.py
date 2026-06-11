"""Shared async Redis client + FastAPI dependency (Phase 8).

A single process-wide `redis.asyncio.Redis` (with its own connection pool, decoded
responses) is the source of truth for the offer TTL (ADR-104) and the accept lock.
`get_redis` is the FastAPI dependency the dispatch router uses; tests override it
with a fakeredis / real-Redis client.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import redis.asyncio as aioredis

from app.core.config import settings

# Process-wide client (lazy pool). `decode_responses=True` so offer payloads are
# str, not bytes — the offer_state wrapper json-loads them directly.
_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Return the process-wide Redis client (created on first use)."""
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def get_redis() -> AsyncIterator[aioredis.Redis]:
    """FastAPI dependency yielding the shared Redis client."""
    yield get_redis_client()
