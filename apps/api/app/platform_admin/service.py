"""Platform-admin cross-area service (REQ-046/047 / D-06/D-07 / TH-02).

Read-mostly cross-area surface for the platform admin. EVERY cross-area read here is
AUDITED (`write_audit(..., cross_area_bypass=True)`) — the bypass is never silent (TH-02
/ RN-001). Filters are bound (no free SQL — TH-06); no PII is read into a log (TH-07).

- `area_overview`: per-area headline counts (couriers/merchants/deliveries) via grouped
  COUNT queries (no N+1).
- `search_couriers` / `search_merchants`: cross-area search with the latest score level
  joined for couriers.
- revenue-share config delegates to `suspensions.service` (parametrised, no money moves).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.models import Area
from app.audit.service import write_audit
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.merchants.models import Merchant
from app.scores.models import CourierScoreSnapshot


async def _audit_cross_area(session: AsyncSession, *, actor_id: int, action: str) -> None:
    """Record a platform-admin cross-area read (TH-02 — never silent)."""
    await write_audit(
        session,
        actor_id=actor_id,
        action=action,
        area_id=None,  # cross-area, no single area
        cross_area_bypass=True,
    )


async def area_overview(session: AsyncSession, *, actor_id: int) -> list[dict]:
    """Per-area headline counts (couriers/merchants/deliveries). Cross-area → audited."""
    await _audit_cross_area(session, actor_id=actor_id, action="platform.area_overview")

    areas = (await session.execute(select(Area).where(Area.deleted_at.is_(None)))).scalars().all()
    courier_counts: dict[int, int] = {
        row[0]: row[1]
        for row in (
            await session.execute(
                select(Courier.area_id, func.count(Courier.id)).group_by(Courier.area_id)
            )
        ).all()
    }
    merchant_counts: dict[int, int] = {
        row[0]: row[1]
        for row in (
            await session.execute(
                select(Merchant.area_id, func.count(Merchant.id)).group_by(Merchant.area_id)
            )
        ).all()
    }
    delivery_counts: dict[int, int] = {
        row[0]: row[1]
        for row in (
            await session.execute(
                select(Delivery.area_id, func.count(Delivery.id)).group_by(Delivery.area_id)
            )
        ).all()
    }
    return [
        {
            "area_id": a.id,
            "codename": a.codename,
            "name": a.name,
            "couriers": int(courier_counts.get(a.id, 0)),
            "merchants": int(merchant_counts.get(a.id, 0)),
            "deliveries": int(delivery_counts.get(a.id, 0)),
        }
        for a in areas
    ]


async def search_couriers(
    session: AsyncSession,
    *,
    actor_id: int,
    q: str | None = None,
    area_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Cross-area courier search with the latest score level (audited)."""
    await _audit_cross_area(session, actor_id=actor_id, action="platform.search_couriers")

    stmt = select(Courier).where(Courier.deleted_at.is_(None))
    if area_id is not None:
        stmt = stmt.where(Courier.area_id == area_id)
    if q:
        # Bound LIKE (TH-06 — parameter, never string-built SQL).
        stmt = stmt.where(Courier.full_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Courier.id.desc()).limit(limit).offset(offset)
    couriers = (await session.execute(stmt)).scalars().all()

    rows: list[dict] = []
    for c in couriers:
        snapshot = (
            await session.execute(
                select(CourierScoreSnapshot)
                .where(CourierScoreSnapshot.courier_id == c.id)
                .order_by(CourierScoreSnapshot.snapshot_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        rows.append(
            {
                "courier_id": c.id,
                "area_id": c.area_id,
                "full_name": c.full_name,
                "status": c.status,
                "score_total": float(snapshot.total_score) if snapshot else None,
                "score_level": snapshot.level if snapshot else None,
            }
        )
    return rows


async def search_merchants(
    session: AsyncSession,
    *,
    actor_id: int,
    q: str | None = None,
    area_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Cross-area merchant search (audited)."""
    await _audit_cross_area(session, actor_id=actor_id, action="platform.search_merchants")

    stmt = select(Merchant)
    if area_id is not None:
        stmt = stmt.where(Merchant.area_id == area_id)
    if q:
        stmt = stmt.where(Merchant.trade_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Merchant.id.desc()).limit(limit).offset(offset)
    merchants = (await session.execute(stmt)).scalars().all()
    return [
        {
            "merchant_id": m.id,
            "area_id": m.area_id,
            "name": m.trade_name,
            "status": m.status,
        }
        for m in merchants
    ]
