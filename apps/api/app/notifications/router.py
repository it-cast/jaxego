"""/v1/push-subscriptions — register/remove a device Web Push subscription (RN-031).

A subscription is the target for the push channel. Registration is contextual (the UI
asks after the first delivery — opt-in, skill push); the body is the browser
subscription JSON. No PII (endpoint + keys are not PII). `commit()` in the router.
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.session import get_session
from app.notifications.models import PushSubscription

router = APIRouter(prefix="/push-subscriptions", tags=["notifications"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class PushSubscriptionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(min_length=1, max_length=512)
    keys: dict[str, str]
    delivery_id: int | None = None
    area_id: int


class PushSubscriptionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    endpoint: str


@router.post("", response_model=PushSubscriptionOut, status_code=status.HTTP_201_CREATED)
async def register_subscription(
    body: PushSubscriptionIn,
    user: CurrentUser,
    session: SessionDep,
) -> PushSubscriptionOut:
    """Register (or refresh) this device's push subscription (opt-in)."""
    existing = (
        (
            await session.execute(
                select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        existing.keys_json = json.dumps(body.keys)
        existing.delivery_id = body.delivery_id
        existing.user_id = user.id
        existing.actor_type = user.type
        await session.commit()
        return PushSubscriptionOut(id=existing.id, endpoint=existing.endpoint)

    sub = PushSubscription(
        area_id=body.area_id,
        user_id=user.id,
        actor_type=user.type,
        delivery_id=body.delivery_id,
        endpoint=body.endpoint,
        keys_json=json.dumps(body.keys),
    )
    session.add(sub)
    await session.commit()
    return PushSubscriptionOut(id=sub.id, endpoint=sub.endpoint)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subscription(
    endpoint: str,
    user: CurrentUser,
    session: SessionDep,
) -> Response:
    """Remove a device subscription by endpoint (opt-out)."""
    await session.execute(
        delete(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user.id,
            PushSubscription.actor_type == user.type,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
