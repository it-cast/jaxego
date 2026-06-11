"""Rating service: post-FINALIZADA, UNIQUE per delivery, merchant scope (T-03 / REQ-033)."""

from __future__ import annotations

import pytest
from app.ratings.service import (
    DeliveryNotFoundError,
    DeliveryNotRatableError,
    RatingExistsError,
    create_rating,
)
from sqlalchemy.ext.asyncio import AsyncSession

from tests.ratings.conftest import RatingWorld


@pytest.mark.asyncio
async def test_create_rating_on_finalizada(
    db_session: AsyncSession, rating_world: RatingWorld
) -> None:
    rating = await create_rating(
        db_session,
        delivery_id=rating_world.delivery_id,
        merchant_id=rating_world.merchant_id,
        area_id=rating_world.area_a_id,
        stars=5,
        comment="Excelente",
    )
    assert rating.id is not None
    assert rating.courier_id == rating_world.courier_id
    assert rating.stars == 5


@pytest.mark.asyncio
async def test_second_rating_for_same_delivery_rejected(
    db_session: AsyncSession, rating_world: RatingWorld
) -> None:
    """UNIQUE per delivery (D-03) — a second rating is a 409, not a silent overwrite."""
    await create_rating(
        db_session,
        delivery_id=rating_world.delivery_id,
        merchant_id=rating_world.merchant_id,
        area_id=rating_world.area_a_id,
        stars=4,
        comment=None,
    )
    with pytest.raises(RatingExistsError):
        await create_rating(
            db_session,
            delivery_id=rating_world.delivery_id,
            merchant_id=rating_world.merchant_id,
            area_id=rating_world.area_a_id,
            stars=1,
            comment="mudei de ideia",
        )


@pytest.mark.asyncio
async def test_other_merchant_cannot_rate(
    db_session: AsyncSession, rating_world: RatingWorld
) -> None:
    """A store that does not own the delivery → 404 (merchant scope, no leak)."""
    with pytest.raises(DeliveryNotFoundError):
        await create_rating(
            db_session,
            delivery_id=rating_world.delivery_id,
            merchant_id=rating_world.other_merchant_id,
            area_id=rating_world.area_b_id,
            stars=5,
            comment=None,
        )


@pytest.mark.asyncio
async def test_cannot_rate_non_finalizada(
    db_session: AsyncSession, rating_world: RatingWorld
) -> None:
    """A delivery that is not FINALIZADA cannot be rated (422)."""
    from app.deliveries.models import Delivery
    from app.neighborhoods.models import Neighborhood
    from sqlalchemy import select

    nbhd = (await db_session.execute(select(Neighborhood))).scalars().first()
    d = Delivery(
        area_id=rating_world.area_a_id,
        merchant_id=rating_world.merchant_id,
        courier_id=rating_world.courier_id,
        state="ENTREGUE",
        pickup_address="Rua A, 1",
        dropoff_address="Rua B, 2",
        dropoff_neighborhood_id=nbhd.id,
        public_token="tok_entregue_01",
    )
    db_session.add(d)
    await db_session.flush()

    with pytest.raises(DeliveryNotRatableError):
        await create_rating(
            db_session,
            delivery_id=d.id,
            merchant_id=rating_world.merchant_id,
            area_id=rating_world.area_a_id,
            stars=5,
            comment=None,
        )
