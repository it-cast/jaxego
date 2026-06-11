"""Rating service (REQ-033 / D-03) — store rates courier after FINALIZADA.

Invariants:
- The delivery must be FINALIZADA (rating only after the delivery concludes).
- The caller's merchant must OWN the delivery (merchant_scope — a store rates only its
  own deliveries; area is in the WHERE clause too).
- One rating per delivery (UNIQUE delivery_id): a second attempt → 409 (not a silent
  overwrite — append, D-03).
- The delivery must have a courier (courier_id NOT NULL).

No PII is read or logged here (TH-07) — only ids and the star/comment payload.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.deliveries.models import Delivery
from app.ratings.models import CourierRating


class DeliveryNotRatableError(AppError):
    """The delivery is not FINALIZADA / not owned / has no courier (422)."""

    status_code = 422
    code = "delivery_not_ratable"

    def __init__(self, message: str = "Entrega não pode ser avaliada.") -> None:
        super().__init__(message)


class DeliveryNotFoundError(AppError):
    """Delivery outside the caller's scope → 404 (never 403; TH-03)."""

    status_code = 404
    code = "delivery_not_found"

    def __init__(self) -> None:
        super().__init__("Entrega não encontrada.")


class RatingExistsError(AppError):
    """The delivery was already rated (one rating per delivery — D-03)."""

    status_code = 409
    code = "rating_exists"

    def __init__(self) -> None:
        super().__init__("Esta entrega já foi avaliada.")


async def create_rating(
    session: AsyncSession,
    *,
    delivery_id: int,
    merchant_id: int,
    area_id: int,
    stars: int,
    comment: str | None,
) -> CourierRating:
    """Create the one rating for a FINALIZADA delivery owned by `merchant_id`."""
    # Ownership + area in the WHERE clause (TH-03 → 404 outside scope).
    delivery = (
        await session.execute(
            select(Delivery).where(
                Delivery.id == delivery_id,
                Delivery.merchant_id == merchant_id,
                Delivery.area_id == area_id,
            )
        )
    ).scalar_one_or_none()
    if delivery is None:
        raise DeliveryNotFoundError()
    if delivery.state != "FINALIZADA":
        raise DeliveryNotRatableError("Avalie somente após a entrega finalizada.")
    if delivery.courier_id is None:
        raise DeliveryNotRatableError("Entrega sem entregador para avaliar.")

    # One rating per delivery (D-03). Check before insert for a clean 409.
    existing = (
        await session.execute(
            select(CourierRating.id).where(CourierRating.delivery_id == delivery_id)
        )
    ).first()
    if existing is not None:
        raise RatingExistsError()

    rating = CourierRating(
        area_id=area_id,
        delivery_id=delivery_id,
        courier_id=delivery.courier_id,
        merchant_id=merchant_id,
        stars=stars,
        comment=comment,
    )
    session.add(rating)
    await session.flush()
    return rating
