"""Plan limit (RN-028 / REQ-011 / LOW-3): Free = 2/month; 3rd blocks with upgrade.

`deliveries_this_month` COUNTs server-side and EXCLUDES CANCELADA (RN-004: a
pre-acceptance cancel costs nothing and must not let a store burn a slot by
create+cancel). The 3rd create on Free raises PlanLimitReachedError (402) with an
upgrade payload; cancelling a created delivery frees a slot.
"""

from __future__ import annotations

import pytest
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


async def _create(seed, db_session):
    return await service.create_delivery(
        db_session,
        area_id=seed.area_a_id,
        merchant_id=seed.merchant_id,
        actor_user_id=seed.owner_user_id,
        body=_body(seed),
        ip=None,
    )


@pytest.mark.asyncio
async def test_free_allows_two_then_blocks_third(delivery_seed, db_session) -> None:
    await _create(delivery_seed, db_session)
    await _create(delivery_seed, db_session)
    with pytest.raises(service.PlanLimitReachedError) as exc:
        await _create(delivery_seed, db_session)
    assert exc.value.status_code in (402, 409)
    # Upgrade payload present (no dark pattern; the UI decides copy).
    assert getattr(exc.value, "plan_code", None) is not None


@pytest.mark.asyncio
async def test_cancelled_delivery_does_not_count(delivery_seed, db_session) -> None:
    r1 = await _create(delivery_seed, db_session)
    await _create(delivery_seed, db_session)
    # Cancel the first → frees a slot.
    await service.cancel_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        delivery_id=r1.delivery_id,
        reason="cliente desistiu",
        ip=None,
    )
    # The 3rd create now succeeds because one of the two is CANCELADA.
    r3 = await _create(delivery_seed, db_session)
    assert r3.delivery_id is not None


@pytest.mark.asyncio
async def test_count_excludes_cancelada(delivery_seed, db_session) -> None:
    r1 = await _create(delivery_seed, db_session)
    await service.cancel_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        delivery_id=r1.delivery_id,
        reason="teste",
        ip=None,
    )
    count = await service.deliveries_this_month(
        db_session, merchant_id=delivery_seed.merchant_id, area_id=delivery_seed.area_a_id
    )
    assert count == 0
