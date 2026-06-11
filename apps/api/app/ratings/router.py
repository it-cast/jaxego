"""/v1/deliveries/{delivery_id}/rating — store rates the courier (REQ-033 / D-03).

The store user is resolved by `merchant_scope` (its (area_id, merchant_id) is pushed
into the service WHERE clause). The rating is allowed only after FINALIZADA and only for
the store's own delivery, exactly once. Input is bound by Pydantic (1..5 — TH-06).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.deliveries.dependencies import MerchantScopeDep
from app.ratings import service
from app.ratings.schemas import RatingCreateBody, RatingRead

router = APIRouter(prefix="/deliveries", tags=["ratings"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/{delivery_id}/rating",
    response_model=RatingRead,
    status_code=status.HTTP_201_CREATED,
)
async def rate_courier(
    delivery_id: int,
    body: RatingCreateBody,
    scope: MerchantScopeDep,
    session: SessionDep,
) -> RatingRead:
    """Rate the courier of a FINALIZADA delivery (1-5 + comment). One per delivery."""
    rating = await service.create_rating(
        session,
        delivery_id=delivery_id,
        merchant_id=scope.merchant_id,
        area_id=scope.area_id,
        stars=body.stars,
        comment=body.comment,
    )
    await session.commit()
    return RatingRead.model_validate(rating)
