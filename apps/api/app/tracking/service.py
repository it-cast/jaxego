"""Append a row to the courier action+location audit log (`delivery_locations`).

One row per real courier action on a delivery, carrying the device GPS at that
moment (CORRECAO-252). The table is append-only (MySQL trigger rejects
UPDATE/DELETE, migration 0048) — this module is the ONLY writer, mirroring how
`app/deliveries/service.py::transition()` is the only writer of
`delivery_state_transitions`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.tracking.models import DeliveryLocation

# Canonical action names (RN-012-like audit trail — never invent a new string
# inline at the call site, add it here so the set stays closed and greppable).
ACTION_ACEITOU = "aceitou"
ACTION_CHEGOU_DESTINO = "chegou_destino"
ACTION_COLETOU = "coletou"
ACTION_ENTREGOU = "entregou"
ACTION_RECUSOU_ENTREGA = "recusou_entrega"
ACTION_CANCELOU_ACEITE = "cancelou_aceite"

COURIER_ACTIONS = frozenset(
    {
        ACTION_ACEITOU,
        ACTION_CHEGOU_DESTINO,
        ACTION_COLETOU,
        ACTION_ENTREGOU,
        ACTION_RECUSOU_ENTREGA,
        ACTION_CANCELOU_ACEITE,
    }
)


async def log_courier_action(
    session: AsyncSession,
    *,
    area_id: int,
    delivery_id: int,
    courier_id: int,
    action: str,
    lat: float | None,
    lng: float | None,
) -> None:
    """Append one audit row. No-op if `lat`/`lng` is missing (nothing to log).

    A missing GPS fix only happens today on the photo-refusal path, where the
    client GPS is not required (`app/proofs/service.py::submit_photo_proof`) —
    every other action REQUIRES lat/lng at the request-schema level, so this
    guard is a defensive no-op there, not a silent gap.
    """
    if lat is None or lng is None:
        return
    assert action in COURIER_ACTIONS, f"unknown courier action: {action!r}"
    session.add(
        DeliveryLocation(
            area_id=area_id,
            delivery_id=delivery_id,
            courier_id=courier_id,
            action=action,
            lat=lat,
            lng=lng,
            recorded_at=datetime.now(UTC),
        )
    )
    await session.flush()
