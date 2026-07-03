"""Courier freight table (REQ-017) — couriers price freely per zone/team.

Pricing floors (piso_entrega / piso_km) were removed — pricing is now handled
per-zone by teams; the courier sets their own price per zone/km-band.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.models import CourierPricingTable
from app.couriers.schemas import PricingRow

logger = structlog.get_logger("couriers.pricing")


async def set_pricing(
    session: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
    mode: str,
    rows: Sequence[PricingRow],
) -> None:
    """Replace the courier's pricing rows (delete + insert, no N+1)."""
    await session.execute(
        delete(CourierPricingTable).where(
            CourierPricingTable.area_id == area_id,
            CourierPricingTable.courier_id == courier_id,
        )
    )
    now = datetime.now(UTC)  # AWARE — TD-010
    new_rows = [
        CourierPricingTable(
            area_id=area_id,
            courier_id=courier_id,
            mode=mode,
            neighborhood_id=row.neighborhood_id if mode == "neighborhood" else None,
            up_to_km=row.up_to_km if mode == "km" else None,
            price=row.price,
            return_pct=row.return_pct,
            created_at=now,
            updated_at=now,
        )
        for row in rows
    ]
    session.add_all(new_rows)
    await session.flush()
    logger.info(
        "courier.pricing.update",
        area_id=area_id,
        courier_id=courier_id,
        mode=mode,
        rows=len(new_rows),
    )


async def list_pricing(
    session: AsyncSession, *, area_id: int, courier_id: int
) -> list[CourierPricingTable]:
    """List the courier's pricing rows (single query, no N+1)."""
    from sqlalchemy import select

    stmt = select(CourierPricingTable).where(
        CourierPricingTable.area_id == area_id,
        CourierPricingTable.courier_id == courier_id,
    )
    return list((await session.execute(stmt)).scalars().all())
