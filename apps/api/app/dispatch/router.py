"""/v1/offers — courier polls the active offer, accepts or declines (F-05).

Every route resolves the courier via `courier_scope` (A01 / TH-4): the
(area_id, courier_id) pair is pushed into the WHERE clause, and only the courier
TARGETED by the current offer may accept (404 `NotOfferTargetError`, never 403).
Accept is the hot path (p95 < 200ms — the push is ENQUEUED, never synchronous).
The offer body carries NO PII (RN-013). `commit()` happens in the router.
"""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_session
from app.deliveries.models import Delivery
from app.dispatch import offer_state, service
from app.dispatch.dependencies import CourierScopeDep
from app.dispatch.exceptions import NotOfferTargetError
from app.dispatch.schemas import (
    AcceptOfferBody,
    AcceptResponse,
    DeclineResponse,
    OfferOut,
    PoolItemOut,
)

router = APIRouter(prefix="/offers", tags=["dispatch"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/active", response_model=OfferOut, responses={204: {"description": "no offer"}})
async def get_active_offer(
    scope: CourierScopeDep,
    session: SessionDep,
    r: RedisDep,
) -> OfferOut | Response:
    """The courier's current offer (Redis is the timer source of truth — ADR-104).

    Returns 204 when there is no live offer. The payload exposes ONLY the dropoff
    neighborhood + distance (RN-013) — never the full destination address.
    """
    delivery_id = await offer_state.active_offer_for_courier(r, scope.courier_id)
    if delivery_id is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    delivery = await session.get(Delivery, delivery_id)
    if delivery is None or delivery.area_id != scope.area_id:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return await service.build_offer_view(session, r, delivery=delivery)


@router.post("/{delivery_id}/accept", response_model=AcceptResponse)
async def accept_offer(
    delivery_id: int,
    body: AcceptOfferBody,
    request: Request,
    scope: CourierScopeDep,
    session: SessionDep,
    r: RedisDep,
) -> AcceptResponse:
    """Accept the offer — single winner via Lock + FOR UPDATE (D-05). 409 if taken."""
    delivery = await service.accept_offer(
        session,
        r,
        area_id=scope.area_id,
        delivery_id=delivery_id,
        courier_id=scope.courier_id,
        actor_user_id=scope.user_id,
        ip=_client_ip(request),
        lat=body.lat,
        lng=body.lng,
    )
    await session.commit()
    # Notify the store + recipient on the queue (never synchronous — skill push).
    from app.dispatch import cascade

    await cascade.enqueue_accept_notifications(delivery_id=delivery.id)
    return AcceptResponse(delivery_id=delivery.id, state=delivery.state)


@router.post("/{delivery_id}/decline", response_model=DeclineResponse)
async def decline_offer(
    delivery_id: int,
    scope: CourierScopeDep,
    session: SessionDep,
    r: RedisDep,
) -> DeclineResponse:
    """Decline the offer — advance the cascade to the next candidate (compare-and-advance)."""
    # Only the targeted courier may decline (A01 — same 404 as accept).
    offer = await offer_state.current_offer(r, delivery_id)
    if offer is None or offer.get("courier_id") != scope.courier_id:
        raise NotOfferTargetError()

    from app.dispatch import cascade

    await cascade.advance_after_decline(
        session, r, area_id=scope.area_id, delivery_id=delivery_id, declined_by=scope.courier_id
    )
    return DeclineResponse(delivery_id=delivery_id, declined=True)


@router.get("/pool", response_model=list[PoolItemOut])
async def list_pool(
    scope: CourierScopeDep,
    session: SessionDep,
) -> list[PoolItemOut]:
    """Deliveries this courier may self-assign from the unanswered pool.

    SEM_RESPOSTA deliveries are those the dispatch cascade exhausted — every
    eligible courier declined or hit the timeout cap. Filtered to the SAME
    coverage + team eligibility the cascade itself applies.
    """
    return await service.list_unanswered_pool(
        session, area_id=scope.area_id, courier_id=scope.courier_id
    )


@router.post("/pool/{delivery_id}/accept", response_model=AcceptResponse)
async def accept_pool_delivery(
    delivery_id: int,
    body: AcceptOfferBody,
    request: Request,
    scope: CourierScopeDep,
    session: SessionDep,
    r: RedisDep,
) -> AcceptResponse:
    """Self-assign a SEM_RESPOSTA delivery — single winner via Lock + FOR UPDATE."""
    delivery = await service.self_assign_pool_delivery(
        session,
        r,
        area_id=scope.area_id,
        delivery_id=delivery_id,
        courier_id=scope.courier_id,
        actor_user_id=scope.user_id,
        ip=_client_ip(request),
        lat=body.lat,
        lng=body.lng,
    )
    await session.commit()
    from app.dispatch import cascade

    await cascade.enqueue_accept_notifications(delivery_id=delivery.id)
    return AcceptResponse(delivery_id=delivery.id, state=delivery.state)


__all__ = ["router"]
