"""Courier availability (REQ-018 / D-06) — online/offline; busy is DERIVED.

Only a courier with status `active` (KYC ok — Phase 5) may go online; a
non-active courier is rejected with 409 (item 6 of the Security Notes — do not
expose availability of someone who cannot operate). `busy` is NOT a column: it is
DERIVED from the load (`compute_busy`) using the area's `max_entregas_simultaneas`
config. The actual active-delivery count arrives from Phase 7/8.
"""

from __future__ import annotations

from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.couriers.models import Courier

logger = structlog.get_logger("couriers.availability")


class CannotGoOnlineError(AppError):
    """A non-active courier cannot go online (409)."""

    status_code = 409
    code = "courier_not_active"

    def __init__(self) -> None:
        super().__init__("Termine sua validação para ficar online e receber ofertas.")


def compute_busy(active_deliveries: int, max_concurrent: int) -> bool:
    """busy iff the courier is at/over capacity (DERIVED — uses area config limit)."""
    return active_deliveries >= max_concurrent


async def _get_scoped(session: AsyncSession, *, area_id: int | None, courier_id: int) -> Courier:
    """Load a courier within the area scope or raise 404 (no existence leak)."""
    stmt = select(Courier).where(Courier.id == courier_id)
    if area_id is not None:
        stmt = stmt.where(Courier.area_id == area_id)
    courier = (await session.execute(stmt)).scalar_one_or_none()
    if courier is None or courier.deleted_at is not None:
        raise NotFoundError("Entregador não encontrado.")
    return courier


async def set_availability(
    session: AsyncSession,
    *,
    area_id: int | None,
    courier_id: int,
    online: bool,
    online_until: datetime | None = None,
) -> Courier:
    """Toggle online/offline. Only an `active` courier may go online (409 else)."""
    courier = await _get_scoped(session, area_id=area_id, courier_id=courier_id)
    if online and courier.status != "active":
        raise CannotGoOnlineError()
    courier.is_online = online
    courier.online_until = online_until if online else None
    await session.flush()
    logger.info(
        "courier.availability.update",
        area_id=area_id,
        courier_id=courier_id,
        online=online,
        online_until=online_until.isoformat() if online_until else None,
    )
    return courier


