"""IDOR / cross-area isolation (TH-03 / A01): store B may not see/cancel store A.

A delivery resolved outside the store's (area_id, merchant_id) returns 404 — not
403, no existence leak. Tests drive the service with the WRONG merchant/area.
"""

from __future__ import annotations

import pytest
from app.core.exceptions import NotFoundError
from app.deliveries import service
from app.deliveries.schemas import CreateDeliveryBody


def _body(seed) -> CreateDeliveryBody:
    return CreateDeliveryBody(
        pickup_address="Rua A, 100",
        pickup_neighborhood="Centro",
        dropoff_neighborhood_id=seed.dropoff_nbhd_id,
        dropoff_address="Rua B, 200",
        dropoff_number="200",
        dropoff_complement=None,
        recipient_name="Maria Cliente",
        recipient_phone_e164="+5522988887777",
        recipient_cpf=None,
        recipient_email=None,
        items_description="1 pizza",
        items_quantity=1,
        declared_value_cents=None,
        reference_number=None,
        notes=None,
        proof_method="photo",
        payment_method="direct",
        distance_m=3000,
    )


@pytest.mark.asyncio
async def test_get_delivery_other_merchant_404(delivery_seed, db_session) -> None:
    created = await service.create_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        body=_body(delivery_seed),
        ip=None,
    )
    # Store B (area B) tries to read store A's delivery → 404.
    with pytest.raises(NotFoundError):
        await service.get_delivery(
            db_session,
            area_id=delivery_seed.area_b_id,
            merchant_id=delivery_seed.other_merchant_id,
            delivery_id=created.delivery_id,
        )


@pytest.mark.asyncio
async def test_cancel_other_merchant_404(delivery_seed, db_session) -> None:
    created = await service.create_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        body=_body(delivery_seed),
        ip=None,
    )
    with pytest.raises(NotFoundError):
        await service.cancel_delivery(
            db_session,
            area_id=delivery_seed.area_b_id,
            merchant_id=delivery_seed.other_merchant_id,
            actor_user_id=delivery_seed.other_owner_user_id,
            delivery_id=created.delivery_id,
            reason="tentando cancelar de outra loja",
            ip=None,
        )


@pytest.mark.asyncio
async def test_list_only_own_deliveries(delivery_seed, db_session) -> None:
    await service.create_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        body=_body(delivery_seed),
        ip=None,
    )
    # Store B lists its own (empty) deliveries — never sees store A's.
    page = await service.list_deliveries(
        db_session,
        area_id=delivery_seed.area_b_id,
        merchant_id=delivery_seed.other_merchant_id,
    )
    assert page.total == 0
    assert page.items == []
