"""Reference-number proof of delivery (E4 / REQ-028 — F-06).

When `proof_method == photo_reference`, the courier types the reference number; it is
compared (case-insensitively, trimmed) against `delivery.reference_number`. A match →
ENTREGUE via `transition()`. 3 wrong attempts → `ReferenceLockedError` orienting the
courier to call the store; the store can then release manually (`manual_release`,
recorded in the transition reason — auditable). Attempts are counted from the
append-only history's prior `photo_reference` failures (a DeliveryProof row per try).

aware-UTC (TD-010). No PII logged (A09).
"""

from __future__ import annotations

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.deliveries.models import Delivery
from app.deliveries.service import transition
from app.proofs.models import DeliveryProof
from app.proofs.schemas import ProofResponse

logger = structlog.get_logger("proofs.reference")

REFERENCE_MAX_ATTEMPTS = 3


class ReferenceMismatchError(AppError):
    """The typed reference number does not match (E4 — actionable counter)."""

    status_code = 422
    code = "reference_mismatch"

    def __init__(self, *, attempts: int) -> None:
        self.attempts = attempts
        remaining = REFERENCE_MAX_ATTEMPTS - attempts
        super().__init__(
            f"Número não confere (tentativa {attempts} de {REFERENCE_MAX_ATTEMPTS}). "
            f"Confirme com o destinatário" + (" ou ligue para a loja." if remaining <= 1 else ".")
        )


class ReferenceLockedError(AppError):
    """3 wrong reference attempts — the courier must call the store (E4)."""

    status_code = 409
    code = "reference_locked"

    def __init__(self) -> None:
        super().__init__(
            "Número não confere após 3 tentativas. Ligue para a loja para liberar a entrega."
        )


def _normalise(value: str) -> str:
    return value.strip().upper()


async def _failed_reference_attempts(session: AsyncSession, *, delivery_id: int) -> int:
    """Count prior FAILED reference proofs (each wrong try records one row)."""
    stmt = select(func.count(DeliveryProof.id)).where(
        DeliveryProof.delivery_id == delivery_id,
        DeliveryProof.proof_kind == "delivery",
        DeliveryProof.method == "photo_reference",
        DeliveryProof.geofence_ok.is_(False),
    )
    return int((await session.execute(stmt)).scalar_one())


async def submit_reference_proof(
    session: AsyncSession,
    *,
    delivery: Delivery,
    actor_user_id: int | None,
    reference_number: str,
    ip: str | None,
    lat: float | None = None,
    lng: float | None = None,
) -> ProofResponse:
    """Validate the reference number → ENTREGUE, or count the failure (E4)."""
    from datetime import UTC, datetime

    prior = await _failed_reference_attempts(session, delivery_id=delivery.id)
    if prior >= REFERENCE_MAX_ATTEMPTS:
        raise ReferenceLockedError()

    expected = delivery.reference_number
    if expected is not None and _normalise(reference_number) == _normalise(expected):
        # Match → record the successful proof + transition to ENTREGUE.
        session.add(
            DeliveryProof(
                area_id=delivery.area_id,
                delivery_id=delivery.id,
                proof_kind="delivery",
                method="photo_reference",
                storage_key=None,
                geofence_ok=True,
                low_confidence=False,
                created_at=datetime.now(UTC),  # AWARE — TD-010
            )
        )
        await session.flush()
        await transition(
            session,
            delivery=delivery,
            to_state="ENTREGUE",
            actor_id=actor_user_id,
            reason="photo_reference",
            ip=ip,
        )
        from app.tracking.service import ACTION_ENTREGOU, log_courier_action

        await log_courier_action(
            session,
            area_id=delivery.area_id,
            delivery_id=delivery.id,
            courier_id=delivery.courier_id,
            action=ACTION_ENTREGOU,
            lat=lat,
            lng=lng,
        )
        logger.info("reference.matched", area_id=delivery.area_id, delivery_id=delivery.id)
        return ProofResponse(
            delivery_id=delivery.id,
            state=delivery.state,
            geofence_ok=True,
            low_confidence=False,
        )

    # Mismatch → record the failed attempt; raise with the rising counter.
    session.add(
        DeliveryProof(
            area_id=delivery.area_id,
            delivery_id=delivery.id,
            proof_kind="delivery",
            method="photo_reference",
            storage_key=None,
            geofence_ok=False,
            low_confidence=False,
            created_at=datetime.now(UTC),
        )
    )
    await session.flush()
    attempts = prior + 1
    if attempts >= REFERENCE_MAX_ATTEMPTS:
        raise ReferenceLockedError()
    raise ReferenceMismatchError(attempts=attempts)


async def manual_release(
    session: AsyncSession,
    *,
    delivery: Delivery,
    actor_user_id: int | None,
    ip: str | None,
) -> None:
    """Store releases the delivery manually after a reference lock (E4 — auditable)."""
    await transition(
        session,
        delivery=delivery,
        to_state="ENTREGUE",
        actor_id=actor_user_id,
        reason="manual_release",  # recorded in the append-only history (auditable)
        ip=ip,
    )
    logger.info("reference.manual_release", area_id=delivery.area_id, delivery_id=delivery.id)
