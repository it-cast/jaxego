"""Webhook endpoint + delivery persistence (area-scoped — TH-03)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhooks.models import WebhookDelivery, WebhookEndpoint


async def get_endpoint_for_area(session: AsyncSession, *, area_id: int) -> WebhookEndpoint | None:
    """The area's single configured endpoint, or None (D-06)."""
    stmt = select(WebhookEndpoint).where(WebhookEndpoint.area_id == area_id)
    return (await session.execute(stmt)).scalars().first()


async def get_delivery(session: AsyncSession, *, delivery_pk: int) -> WebhookDelivery | None:
    """Load a webhook delivery by its PK (the job re-reads under no lock — idempotent)."""
    return await session.get(WebhookDelivery, delivery_pk)


async def list_deliveries_for_area(
    session: AsyncSession, *, area_id: int, limit: int, offset: int
) -> tuple[list[WebhookDelivery], int]:
    """Paginated webhook-delivery history for the area (screen 22)."""
    from sqlalchemy import func

    base = (
        select(WebhookDelivery)
        .where(WebhookDelivery.area_id == area_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list((await session.execute(base)).scalars().all())
    total = int(
        (
            await session.execute(
                select(func.count(WebhookDelivery.id)).where(WebhookDelivery.area_id == area_id)
            )
        ).scalar_one()
    )
    return rows, total


async def due_deliveries(
    session: AsyncSession, *, now: datetime, limit: int = 100
) -> list[WebhookDelivery]:
    """Pending deliveries whose next_retry_at has arrived (sweep — used by the cron)."""
    stmt = (
        select(WebhookDelivery)
        .where(
            WebhookDelivery.status == "pending",
            WebhookDelivery.next_retry_at <= now,
        )
        .order_by(WebhookDelivery.next_retry_at.asc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())
