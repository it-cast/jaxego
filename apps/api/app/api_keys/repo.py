"""API key + idempotency persistence (area-scoped — TH-03).

Every query is scoped by `area_id` so a key/snapshot from another area is simply
not visible (IDOR closed by construction). The idempotency lookup uses
`with_for_update()` so two concurrent replays of the same key serialize.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys.models import ApiIdempotencyKey, ApiKey


async def get_by_key_id(session: AsyncSession, *, key_id: str) -> ApiKey | None:
    """Fetch a key by its public lookup handle (any area — auth resolves the area)."""
    stmt = select(ApiKey).where(ApiKey.key_id == key_id)
    return (await session.execute(stmt)).scalars().first()


async def get_for_area(session: AsyncSession, *, area_id: int, key_pk: int) -> ApiKey | None:
    """Fetch a key owned by THIS area, or None (404 cross-area — TH-03)."""
    stmt = select(ApiKey).where(ApiKey.id == key_pk, ApiKey.area_id == area_id)
    return (await session.execute(stmt)).scalars().first()


async def list_for_area(
    session: AsyncSession, *, area_id: int, limit: int, offset: int
) -> list[ApiKey]:
    """List the area's keys, newest first (screen 22)."""
    stmt = (
        select(ApiKey)
        .where(ApiKey.area_id == area_id)
        .order_by(ApiKey.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_for_area(session: AsyncSession, *, area_id: int) -> int:
    from sqlalchemy import func

    stmt = select(func.count(ApiKey.id)).where(ApiKey.area_id == area_id)
    return int((await session.execute(stmt)).scalar_one())


async def get_idempotency_locked(
    session: AsyncSession, *, api_key_id: int, idempotency_key: str
) -> ApiIdempotencyKey | None:
    """Lock-and-fetch the snapshot for (api_key_id, idempotency_key) — replay guard.

    `with_for_update()` serializes concurrent replays of the same key so the second
    request blocks until the first commits its snapshot, then reads it (no double
    create — D-04 / TH-04).
    """
    stmt = (
        select(ApiIdempotencyKey)
        .where(
            ApiIdempotencyKey.api_key_id == api_key_id,
            ApiIdempotencyKey.idempotency_key == idempotency_key,
        )
        .with_for_update()
    )
    return (await session.execute(stmt)).scalars().first()


async def purge_expired_idempotency(session: AsyncSession, *, now: datetime) -> int:
    """Delete idempotency snapshots whose 24h window has elapsed (T-05). Returns count."""
    from sqlalchemy import delete

    result = await session.execute(
        delete(ApiIdempotencyKey).where(ApiIdempotencyKey.expires_at < now)
    )
    return int(result.rowcount or 0)  # pyright: ignore[reportAttributeAccessIssue]
