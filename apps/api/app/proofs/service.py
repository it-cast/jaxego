"""Proof pipeline — fetch RAW → EXIF → geofence → strip → B2 → transition (T-03).

THE OPPOSITE OF THE KYC PIPELINE. The mandatory order (Pitfall 1):

  (a) fetch RAW from B2 (StoragePort.fetch)
  (b) magic bytes + size (reuse media/validation.py)
  (c) extract_gps_from_raw(raw)  ← BEFORE any reprocess (EXIF is destroyed by strip)
      …but the client `{lat,lng}` is the PRIMARY evidence (A3 contract); EXIF reinforces
  (d) within_radius (server-side geofence — the authority, never the GPS itself)
  (e) ≤ radius? OK : reject; count failures, 3rd → low_confidence + CTA unlocks
  (f) reprocess_to_webp (STRIP) → B2 derivative   ← only now
  (g) transition() with gps=(lat,lng) for auditoria (RN-012)

`reprocess_to_webp` is NEVER called before (c). Ownership: only the courier the
delivery is assigned to may submit (404 if not — A01 / TH-1). aware-UTC (TD-010).
"""

from __future__ import annotations

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.config_schema import AreaConfig
from app.areas.models import Area
from app.core.exceptions import AppError, NotFoundError
from app.deliveries.models import Delivery
from app.deliveries.service import transition
from app.integrations.base import StoragePort
from app.media.reprocess import reprocess_to_webp
from app.media.validation import assert_size, sniff_content_type
from app.proofs.exif import extract_gps_from_raw
from app.proofs.geofence import distance_m
from app.proofs.models import DeliveryProof

logger = structlog.get_logger("proofs.service")

# 3 failed geofence checks → low_confidence + admin review (RN-005 / ADR-008).
LOW_CONFIDENCE_THRESHOLD = 3


class GpsMissingError(AppError):
    """No usable GPS (neither client {lat,lng} nor EXIF) — E1, actionable."""

    status_code = 422
    code = "gps_missing"

    def __init__(self) -> None:
        super().__init__("Não conseguimos a sua localização. Ative o GPS e tire a foto de novo.")


class OutOfGeofenceError(AppError):
    """The proof point is outside the area's geofence radius (E1 — TH-1)."""

    status_code = 422
    code = "out_of_geofence"

    def __init__(self, *, failed_attempts: int) -> None:
        self.failed_attempts = failed_attempts
        super().__init__("Você está fora do raio do endereço. Aproxime-se e tire a foto de novo.")


class UnsupportedProofKindError(AppError):
    status_code = 422
    code = "unsupported_proof_kind"

    def __init__(self) -> None:
        super().__init__("Tipo de comprovação inválido.")


async def get_delivery_for_courier(
    session: AsyncSession, *, delivery_id: int, courier_id: int
) -> Delivery:
    """Load the delivery assigned to THIS courier, or 404 (A01 / TH-1)."""
    stmt = select(Delivery).where(
        Delivery.id == delivery_id,
        Delivery.courier_id == courier_id,
    )
    delivery = (await session.execute(stmt)).scalars().first()
    if delivery is None:
        raise NotFoundError("Entrega não encontrada.")
    return delivery


async def _area_config(session: AsyncSession, area_id: int) -> AreaConfig:
    """Typed area config (geofence_m); defaults if unset/invalid (Phase 6)."""
    area = await session.get(Area, area_id)
    raw = dict(area.config) if area and area.config else {}
    try:
        return AreaConfig(**raw)
    except Exception:  # noqa: BLE001 — never wedge a proof on a bad config row
        return AreaConfig()


async def _failed_geofence_attempts(
    session: AsyncSession, *, delivery_id: int, proof_kind: str
) -> int:
    """Count prior FAILED geofence proofs of this kind (for the 3-strike rule)."""
    stmt = select(func.count(DeliveryProof.id)).where(
        DeliveryProof.delivery_id == delivery_id,
        DeliveryProof.proof_kind == proof_kind,
        DeliveryProof.geofence_ok.is_(False),
        DeliveryProof.low_confidence.is_(False),
    )
    return int((await session.execute(stmt)).scalar_one())


def _target_point(delivery: Delivery, proof_kind: str) -> tuple[float, float] | None:
    """The POINT to geofence against: pickup for pickup, dropoff otherwise."""
    if proof_kind == "pickup":
        if delivery.pickup_lat is None or delivery.pickup_lng is None:
            return None
        return delivery.pickup_lat, delivery.pickup_lng
    if delivery.dropoff_lat is None or delivery.dropoff_lng is None:
        return None
    return delivery.dropoff_lat, delivery.dropoff_lng


async def submit_photo_proof(
    session: AsyncSession,
    storage: StoragePort,
    *,
    delivery: Delivery,
    actor_user_id: int | None,
    proof_kind: str,
    storage_key: str,
    client_lat: float | None,
    client_lng: float | None,
    refusal_reason: str | None,
    ip: str | None,
) -> DeliveryProof:
    """Run the mandatory pipeline and (if OK or low_confidence) transition (T-03).

    Returns the persisted DeliveryProof. Raises GpsMissingError / OutOfGeofenceError
    (E1) on a failure that does not yet reach low_confidence.
    """
    if proof_kind not in ("pickup", "delivery", "refusal"):
        raise UnsupportedProofKindError()

    # (a) fetch RAW
    raw = await storage.fetch(storage_key)
    # (b) magic bytes + size — bytes are never trusted (TH-2)
    assert_size(raw)
    from app.media.validation import UnsupportedMediaError

    if sniff_content_type(raw) is None:
        raise UnsupportedMediaError()

    # (c) EXIF GPS from the RAW — BEFORE any reprocess. Client {lat,lng} is primary
    #     evidence (A3); EXIF reinforces / is the fallback when client GPS absent.
    exif_gps = extract_gps_from_raw(raw)
    if client_lat is not None and client_lng is not None:
        gps: tuple[float, float] | None = (client_lat, client_lng)
    else:
        gps = exif_gps

    # Refusal proofs (E3) require a photo + reason but do not have to be in-radius
    # (the courier IS at the destination but the recipient refused/was absent); we
    # still record the GPS when present. For pickup/delivery the geofence is the
    # antifraud barrier.
    geofence_ok = False
    dist: float | None = None
    low_confidence = False
    target = _target_point(delivery, "delivery" if proof_kind == "refusal" else proof_kind)

    if proof_kind in ("pickup", "delivery"):
        if gps is None:
            raise GpsMissingError()
        if target is None:
            # No POINT to validate against — degrade to low_confidence (admin review)
            # rather than block forever (the area has no coordinate for this point).
            low_confidence = True
        else:
            # (d) server-side geofence (the authority)
            dist = await distance_m(
                session, lat=gps[0], lng=gps[1], target_lat=target[0], target_lng=target[1]
            )
            cfg = await _area_config(session, delivery.area_id)
            geofence_ok = dist <= cfg.geofence_m
            if not geofence_ok:
                # (e) count failures; the 3rd unlocks low_confidence (CTA destrava)
                prior = await _failed_geofence_attempts(
                    session, delivery_id=delivery.id, proof_kind=proof_kind
                )
                attempts = prior + 1
                if attempts < LOW_CONFIDENCE_THRESHOLD:
                    # Record the failed attempt (no derivative stored, no transition).
                    proof = DeliveryProof(
                        area_id=delivery.area_id,
                        delivery_id=delivery.id,
                        proof_kind=proof_kind,
                        method="photo",
                        storage_key=None,
                        geofence_ok=False,
                        low_confidence=False,
                        gps_lat=gps[0],
                        gps_lng=gps[1],
                        distance_m=dist,
                        created_at=_now(),
                    )
                    session.add(proof)
                    await session.flush()
                    raise OutOfGeofenceError(failed_attempts=attempts)
                low_confidence = True

    # (f) reprocess + STRIP → B2 derivative — ONLY now (after GPS was read)
    derived, sha = reprocess_to_webp(raw)
    derived_key = f"{storage_key}.webp"
    await storage.put_bytes(derived_key, derived, content_type="image/webp")

    proof = DeliveryProof(
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        proof_kind=proof_kind,
        method="photo",
        storage_key=derived_key,
        sha256=sha,
        geofence_ok=geofence_ok,
        low_confidence=low_confidence,
        gps_lat=gps[0] if gps else None,
        gps_lng=gps[1] if gps else None,
        distance_m=dist,
        refusal_reason=refusal_reason if proof_kind == "refusal" else None,
        created_at=_now(),
    )
    session.add(proof)
    await session.flush()

    # (g) transition — pickup→COLETADA, delivery→ENTREGUE, refusal→RECUSADA.
    await _transition_for_proof(
        session,
        delivery=delivery,
        proof_kind=proof_kind,
        actor_user_id=actor_user_id,
        gps=gps,
        refusal_reason=refusal_reason,
        ip=ip,
    )
    logger.info(
        "proof.submitted",
        area_id=delivery.area_id,
        delivery_id=delivery.id,
        proof_kind=proof_kind,
        geofence_ok=geofence_ok,
        low_confidence=low_confidence,
    )
    return proof


async def _transition_for_proof(
    session: AsyncSession,
    *,
    delivery: Delivery,
    proof_kind: str,
    actor_user_id: int | None,
    gps: tuple[float, float] | None,
    refusal_reason: str | None,
    ip: str | None,
) -> None:
    """Map the proof kind to the F-06 transition (reuse Phase 7 transition())."""
    if proof_kind == "pickup":
        to_state, reason = "COLETADA", None
    elif proof_kind == "delivery":
        to_state, reason = "ENTREGUE", None
    else:  # refusal
        to_state, reason = "RECUSADA_NO_DESTINO", (refusal_reason or "refused")
    await transition(
        session,
        delivery=delivery,
        to_state=to_state,
        actor_id=actor_user_id,
        reason=reason,
        gps=gps,
        ip=ip,
    )


def _now():
    from datetime import UTC, datetime

    return datetime.now(UTC)  # AWARE — TD-010
