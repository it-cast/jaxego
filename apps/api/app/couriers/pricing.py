"""Courier freight table (RN-015 / REQ-017) — floor guard-rail, never a fixed price.

The platform NEVER fixes the price. The courier sets it freely ABOVE the area
floor; a price BELOW the floor is rejected with a 422 whose MESSAGE CITES the
floor (the ROADMAP acceptance criterion). Mode 'neighborhood' validates
`piso_entrega`; mode 'km' validates `piso_km`. Both pisos come from the area's
typed `AreaConfig` (Plan 01).

LOW-5: a later floor increase does NOT retroactively block rows already saved —
only a new submit validates (TD-018, sinalizar não bloquear).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.config_schema import AreaConfig
from app.areas.models import Area
from app.core.exceptions import AppError, NotFoundError
from app.couriers.models import CourierPricingTable
from app.couriers.schemas import PricingRow

logger = structlog.get_logger("couriers.pricing")


class PriceBelowFloorError(AppError):
    """A pricing row is below the area floor (422). The message CITES the floor."""

    status_code = 422
    code = "price_below_floor"

    def __init__(self, *, floor: Decimal, kind: str) -> None:
        unit = "por km" if kind == "km" else "por entrega"
        super().__init__(f"Preço abaixo do piso da área ({unit}): mínimo R$ {floor:.2f}.")


def assert_above_floor(
    price: Decimal | float,
    *,
    floor_km: Decimal | float,
    floor_entrega: Decimal | float,
    mode: str,
) -> None:
    """Reject a price below the floor for its mode (RN-015 — cites the floor)."""
    price_d = Decimal(str(price))
    if mode == "km" and price_d < Decimal(str(floor_km)):
        raise PriceBelowFloorError(floor=Decimal(str(floor_km)), kind="km")
    if mode == "neighborhood" and price_d < Decimal(str(floor_entrega)):
        raise PriceBelowFloorError(floor=Decimal(str(floor_entrega)), kind="neighborhood")


async def _area_floors(session: AsyncSession, *, area_id: int) -> tuple[Decimal, Decimal]:
    """Read (piso_km, piso_entrega) from the area's typed config."""
    area = await session.get(Area, area_id)
    if area is None or area.deleted_at is not None:
        raise NotFoundError("Área não encontrada.")
    cfg = AreaConfig(**(area.config or {}))
    return cfg.piso_km, cfg.piso_entrega


async def set_pricing(
    session: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
    mode: str,
    rows: Sequence[PricingRow],
) -> None:
    """Replace the courier's pricing rows after validating EACH against the floor.

    The platform only imposes the floor (it never fixes the price). Every row is
    checked with `assert_above_floor`; the first row below the floor raises 422
    citing the floor. Rows are written area-scoped (delete + insert, no N+1).
    """
    floor_km, floor_entrega = await _area_floors(session, area_id=area_id)

    for row in rows:
        assert_above_floor(row.price, floor_km=floor_km, floor_entrega=floor_entrega, mode=mode)

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
