"""Public create-delivery orchestration (F-04) — auth+idempotency over the SAME service.

The flow (D-04 / TH-04):
  1. canonicalise the request body → SHA-256 `request_hash`
  2. lock the `(api_key_id, idempotency_key)` snapshot FOR UPDATE
     - exists + same hash → return the cached response (replay, no second create)
     - exists + different hash → 409 (key reuse with a different body)
  3. resolve the target store WITHIN the key's area (404 cross-area — TH-03)
  4. call `deliveries.service.create_delivery` (the SAME state machine)
  5. persist the 24h response snapshot, return the response

The store is NEVER resolved outside the key's `area_id` (IDOR closed by the WHERE).
PII (recipient phone/address) is NEVER logged (TH-09).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys import repo as key_repo
from app.api_keys.models import ApiIdempotencyKey
from app.api_public.schemas import PublicCreateDeliveryBody, PublicDeliveryResponse
from app.core.exceptions import AppError
from app.deliveries import service as delivery_service
from app.deliveries.schemas import CreateDeliveryBody
from app.merchants.models import Merchant

# Idempotency snapshot lifetime (ADR-010 / D-04).
IDEMPOTENCY_TTL = timedelta(hours=24)


class IdempotencyConflictError(AppError):
    """Same Idempotency-Key, different request body (D-04 → 409)."""

    status_code = 409
    code = "idempotency_key_conflict"

    def __init__(self) -> None:
        super().__init__("Idempotency-Key já usada com um corpo de requisição diferente.")


class StoreNotResolvableError(AppError):
    """No store in the key's area matches the target (D-03 → 404, no existence leak)."""

    status_code = 404
    code = "merchant_not_found"

    def __init__(self) -> None:
        super().__init__("Loja não encontrada para esta chave de API.")


def canonical_request_hash(body: PublicCreateDeliveryBody) -> str:
    """SHA-256 (hex) of the canonical JSON body — distinguishes replay from reuse."""
    canonical = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def _resolve_merchant(
    session: AsyncSession, *, area_id: int, body: PublicCreateDeliveryBody
) -> Merchant:
    """Resolve the target store WITHIN the key's area (404 cross-area — TH-03)."""
    stmt = select(Merchant).where(Merchant.area_id == area_id)
    if body.merchant_external_ref is not None:
        stmt = stmt.where(Merchant.external_ref == body.merchant_external_ref)
    else:
        stmt = stmt.where(Merchant.id == body.merchant_id)
    merchant = (await session.execute(stmt)).scalars().first()
    if merchant is None:
        raise StoreNotResolvableError()
    return merchant


def _to_internal_body(body: PublicCreateDeliveryBody) -> CreateDeliveryBody:
    """Map the public body onto the internal create contract (drops store-target fields)."""
    return CreateDeliveryBody(
        pickup_address=body.pickup_address,
        pickup_neighborhood=body.pickup_neighborhood,
        dropoff_neighborhood_id=body.dropoff_neighborhood_id,
        dropoff_address=body.dropoff_address,
        dropoff_number=body.dropoff_number,
        dropoff_complement=body.dropoff_complement,
        distance_m=body.distance_m,
        recipient_name=body.recipient_name,
        recipient_phone_e164=body.recipient_phone_e164,
        recipient_email=body.recipient_email,
        recipient_cpf=body.recipient_cpf,
        items_description=body.items_description,
        items_quantity=body.items_quantity,
        declared_value_cents=body.declared_value_cents,
        reference_number=body.reference_number,
        notes=body.notes,
        proof_method=body.proof_method,
        payment_method=body.payment_method,
    )


async def create_public_delivery(
    session: AsyncSession,
    *,
    area_id: int,
    api_key_id: int,
    idempotency_key: str,
    body: PublicCreateDeliveryBody,
    ip: str | None,
) -> tuple[int, PublicDeliveryResponse, bool]:
    """Create (or replay) a delivery. Returns (status_code, response, replayed)."""
    request_hash = canonical_request_hash(body)

    # Replay guard: lock the snapshot row for this (key, idempotency_key).
    existing = await key_repo.get_idempotency_locked(
        session, api_key_id=api_key_id, idempotency_key=idempotency_key
    )
    if existing is not None:
        if existing.request_hash != request_hash:
            raise IdempotencyConflictError()
        cached = PublicDeliveryResponse.model_validate(json.loads(existing.response_body))
        return existing.response_status, cached, True

    merchant = await _resolve_merchant(session, area_id=area_id, body=body)

    result = await delivery_service.create_delivery(
        session,
        area_id=area_id,
        merchant_id=merchant.id,
        actor_user_id=None,  # the integrator is the actor; no platform user
        body=_to_internal_body(body),
        ip=ip,
    )
    response = PublicDeliveryResponse(
        delivery_id=result.delivery_id,
        public_token=result.public_token,
        state=result.state,
        estimate_min_cents=result.estimate_min_cents,
        estimate_max_cents=result.estimate_max_cents,
        fee_cents=result.fee_cents,
        no_couriers_warning=result.no_couriers_warning,
    )

    snapshot = ApiIdempotencyKey(
        area_id=area_id,
        api_key_id=api_key_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_status=201,
        response_body=response.model_dump_json(),
        delivery_id=result.delivery_id,
        expires_at=datetime.now(UTC) + IDEMPOTENCY_TTL,
    )
    session.add(snapshot)
    await session.flush()
    return 201, response, False
