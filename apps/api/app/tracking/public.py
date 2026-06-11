"""GET /v1/public/tracking/{public_token} — tracking WITHOUT auth (TH-3 / TH-6).

# público: this is the ONLY unauthenticated read endpoint. Access is by the opaque,
non-sequential `public_token` (Crockford 26ch ≈130 bits — `_new_public_token`), not
a credential. An invalid token → 404 GENÉRICO (anti-enumeração — never reveals
existence). Rate-limited per IP (TH-6). The response is built by `serialize_public`,
which minimises PII by state (RN-013/RN-022) — the courier is anonymous, the dropoff
address only appears after COLETADA, and no recipient phone is ever emitted publicly.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.ratelimit import SlidingWindowLimiter, _client_ip
from app.couriers.models import Courier
from app.db.session import get_session
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.tracking.models import DeliveryLocation
from app.tracking.serializer import serialize_public

router = APIRouter(prefix="/public", tags=["public-tracking"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Public tracking: 60/min per IP — anti-enumeration without hurting a real viewer
# refreshing every ~60s (TH-6). In-process limiter (pilot scale).
public_tracking_limiter = SlidingWindowLimiter(limit=60, window=timedelta(minutes=1))


async def public_tracking_rate_limit(request: Request) -> None:
    """Per-IP rate limit for the public tracker (TH-6)."""
    public_tracking_limiter.check(_client_ip(request))


async def _build_timeline(session: AsyncSession, delivery_id: int) -> list[dict[str, object]]:
    """Ordered (to_state, at) milestones from the append-only history (no N+1)."""
    stmt = (
        select(DeliveryStateTransition.to_state, DeliveryStateTransition.created_at)
        .where(DeliveryStateTransition.delivery_id == delivery_id)
        .order_by(DeliveryStateTransition.created_at.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {"state": to_state, "at": created_at.isoformat() if created_at else None}
        for to_state, created_at in rows
    ]


async def _last_location(session: AsyncSession, delivery_id: int) -> DeliveryLocation | None:
    stmt = (
        select(DeliveryLocation)
        .where(DeliveryLocation.delivery_id == delivery_id)
        .order_by(DeliveryLocation.recorded_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


@router.get(
    "/tracking/{public_token}",
    dependencies=[Depends(public_tracking_rate_limit)],
)
async def public_tracking(public_token: str, session: SessionDep) -> dict[str, object]:
    """Public, token-only tracking. Invalid token → 404 genérico (anti-enumeração)."""
    delivery = (
        (await session.execute(select(Delivery).where(Delivery.public_token == public_token)))
        .scalars()
        .first()
    )
    if delivery is None:
        # Generic 404 — never reveals whether the token exists (TH-3 / TH-6).
        raise NotFoundError("Acompanhamento não encontrado.")

    timeline = await _build_timeline(session, delivery.id)
    loc = await _last_location(session, delivery.id)

    vehicle_type: str | None = None
    if delivery.courier_id is not None:
        courier = await session.get(Courier, delivery.courier_id)
        vehicle_type = courier.vehicle_type if courier else None

    return serialize_public(
        state=delivery.state,
        timeline=timeline,
        eta_seconds=None,  # ETA derivation is a UI/routing concern (degrades to None)
        dropoff_neighborhood_id=delivery.dropoff_neighborhood_id,
        dropoff_address=delivery.dropoff_address,
        dropoff_number=delivery.dropoff_number,
        dropoff_complement=delivery.dropoff_complement,
        courier_vehicle_type=vehicle_type,
        last_lat=loc.lat if loc else None,
        last_lng=loc.lng if loc else None,
    )


__all__ = ["router"]
