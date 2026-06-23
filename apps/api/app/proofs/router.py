"""/v1/deliveries/{id}/proof — courier submits photo/reference proof (F-06).

Operated by the COURIER assigned to the delivery (A01 / TH-1): ownership is pushed
into the WHERE clause (`get_delivery_for_courier`) → 404 if not the assignee, never
403. The photo is uploaded to B2 by a presigned PUT first; the submit carries the
`storage_key` + explicit client GPS (A3 contract). `commit()` happens in the router.
The body never carries recipient PII; nothing PII is logged (TH-8 / A09).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.constants import MAX_UPLOAD_BYTES  # noqa: F401 (size budget shared)
from app.db.session import get_session
from app.deliveries.dependencies import MerchantScopeDep
from app.dispatch.dependencies import CourierScopeDep
from app.integrations.factory import get_storage_adapter
from app.proofs import service
from app.proofs.schemas import (
    ProofPresignRequest,
    ProofPresignResponse,
    ProofResponse,
    SubmitProofRequest,
    SubmitReferenceRequest,
)

router = APIRouter(prefix="/deliveries", tags=["proofs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Proof photos live under a per-delivery prefix in the private bucket.
_PROOF_PRESIGN_TTL = 300


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _ext(content_type: str) -> str:
    return {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]


@router.post("/{delivery_id}/proof/presign", response_model=ProofPresignResponse)
async def presign_proof(
    delivery_id: int,
    body: ProofPresignRequest,
    scope: CourierScopeDep,
    session: SessionDep,
) -> ProofPresignResponse:
    """Presign a PUT to upload a proof photo (only the assigned courier — 404)."""
    delivery = await service.get_delivery_for_courier(
        session, delivery_id=delivery_id, courier_id=scope.courier_id
    )
    storage = get_storage_adapter()
    import secrets

    key = f"proofs/{delivery.id}/{secrets.token_hex(8)}.{_ext(body.content_type)}"
    pres = await storage.presign_put(
        key, content_type=body.content_type, expires_in=_PROOF_PRESIGN_TTL
    )
    return ProofPresignResponse(
        storage_key=key,
        upload_url=pres.url,
        method=pres.method,
        headers=pres.headers,
        expires_in=pres.expires_in,
    )


@router.post("/{delivery_id}/proof", response_model=ProofResponse)
async def submit_proof(
    delivery_id: int,
    body: SubmitProofRequest,
    request: Request,
    scope: CourierScopeDep,
    session: SessionDep,
) -> ProofResponse:
    """Submit a pickup/delivery/refusal photo proof (geofence server-side)."""
    delivery = await service.get_delivery_for_courier(
        session, delivery_id=delivery_id, courier_id=scope.courier_id
    )
    storage = get_storage_adapter()
    proof = await service.submit_photo_proof(
        session,
        storage,
        delivery=delivery,
        actor_user_id=scope.user_id,
        proof_kind=body.proof_kind,
        storage_key=body.storage_key,
        client_lat=body.lat,
        client_lng=body.lng,
        refusal_reason=body.refusal_reason,
        ip=_client_ip(request),
    )
    # If delivery just became ENTREGUE, finalize immediately.
    if delivery.state == "ENTREGUE":
        from app.deliveries.service import transition

        await transition(
            session, delivery=delivery, to_state="FINALIZADA",
            actor_id=scope.user_id, reason="immediate_finalize", ip=_client_ip(request),
        )
    await session.commit()
    # Notify the recipient on the queue (a caminho / entregue — never inline).
    from app.notifications.dispatcher import enqueue_notification

    moment = {"pickup": "on_the_way", "delivery": "delivered"}.get(body.proof_kind)
    if moment is not None:
        await enqueue_notification(delivery_id=delivery.id, moment=moment)
    return ProofResponse(
        delivery_id=delivery.id,
        state=delivery.state,
        geofence_ok=proof.geofence_ok,
        low_confidence=proof.low_confidence,
    )


@router.post("/{delivery_id}/proof/reference", response_model=ProofResponse)
async def submit_reference(
    delivery_id: int,
    body: SubmitReferenceRequest,
    request: Request,
    scope: CourierScopeDep,
    session: SessionDep,
) -> ProofResponse:
    """Submit a reference number as proof of delivery (E4 — 3 strikes → call store)."""
    from app.proofs.reference import submit_reference_proof

    delivery = await service.get_delivery_for_courier(
        session, delivery_id=delivery_id, courier_id=scope.courier_id
    )
    result = await submit_reference_proof(
        session,
        delivery=delivery,
        actor_user_id=scope.user_id,
        reference_number=body.reference_number,
        ip=_client_ip(request),
    )
    if result.state == "ENTREGUE":
        from app.deliveries.service import transition

        await transition(
            session, delivery=delivery, to_state="FINALIZADA",
            actor_id=scope.user_id, reason="immediate_finalize", ip=_client_ip(request),
        )
        result = ProofResponse(
            delivery_id=delivery.id, state=delivery.state,
            geofence_ok=result.geofence_ok, low_confidence=result.low_confidence,
        )
    await session.commit()
    if delivery.state == "FINALIZADA" or result.state == "ENTREGUE":
        from app.notifications.dispatcher import enqueue_notification

        await enqueue_notification(delivery_id=delivery.id, moment="delivered")
    return result


@router.post("/{delivery_id}/proof/validate-reference")
async def validate_reference(
    delivery_id: int,
    body: SubmitReferenceRequest,
    scope: CourierScopeDep,
    session: SessionDep,
) -> dict:
    """Validate a reference number WITHOUT transitioning state. Returns valid: true/false."""
    delivery = await service.get_delivery_for_courier(
        session, delivery_id=delivery_id, courier_id=scope.courier_id
    )
    expected = delivery.reference_number
    if expected is None:
        return {"valid": True}
    from app.proofs.reference import _normalise
    valid = _normalise(body.reference_number) == _normalise(expected)
    return {"valid": valid}


@router.post("/{delivery_id}/proof/manual-release", response_model=ProofResponse)
async def manual_release_delivery(
    delivery_id: int,
    request: Request,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> ProofResponse:
    """Store releases a reference-locked delivery manually (E4 — auditable)."""
    from app.deliveries.service import get_delivery
    from app.proofs.reference import manual_release

    delivery = await get_delivery(
        session, area_id=scope.area_id, merchant_id=scope.merchant_id, delivery_id=delivery_id
    )
    await manual_release(
        session, delivery=delivery, actor_user_id=scope.user_id, ip=_client_ip(request)
    )
    await session.commit()
    return ProofResponse(
        delivery_id=delivery.id, state=delivery.state, geofence_ok=True, low_confidence=False
    )


__all__ = ["router"]
