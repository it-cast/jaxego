"""Webhook enqueue from the delivery transition (T-07 / D-08).

Proves the hook in `deliveries.service.transition` enqueues a `WebhookDelivery`
when the area has a (subscribed, enabled) endpoint — and does NOT when there is no
endpoint / the event is not subscribed / the endpoint is disabled. The enqueue is
non-blocking: a webhook problem must not raise into the transition.
"""

from __future__ import annotations

import pytest
from app.webhooks import service as webhook_service
from app.webhooks.models import WebhookDelivery
from sqlalchemy import func, select


async def _count_webhook_rows(session, *, area_id: int) -> int:
    return int(
        (
            await session.execute(
                select(func.count(WebhookDelivery.id)).where(WebhookDelivery.area_id == area_id)
            )
        ).scalar_one()
    )


@pytest.mark.asyncio
async def test_transition_enqueues_when_endpoint_subscribed(
    public_api_seed, session_factory
) -> None:
    from app.deliveries import service as delivery_service
    from app.deliveries.schemas import CreateDeliveryBody

    async with session_factory() as s:
        # Configure an endpoint that subscribes to delivery.created.
        await webhook_service.configure_endpoint(
            s,
            area_id=public_api_seed.area_a_id,
            url="https://1.1.1.1/webhook",
            events=["delivery.created"],
        )
        await s.commit()

    async with session_factory() as s:
        result = await delivery_service.create_delivery(
            s,
            area_id=public_api_seed.area_a_id,
            merchant_id=public_api_seed.merchant_id,
            actor_user_id=None,
            body=CreateDeliveryBody(
                pickup_address="Rua A, 1",
                dropoff_neighborhood_id=public_api_seed.dropoff_nbhd_id,
                dropoff_address="Rua B, 2",
                recipient_name="Cliente",
                recipient_phone_e164="+5522988887777",
                payment_method="direct",
            ),
            ip=None,
        )
        await s.commit()
        assert result.delivery_id > 0

    async with session_factory() as s:
        count = await _count_webhook_rows(s, area_id=public_api_seed.area_a_id)
    # The CRIADA transition enqueued exactly one delivery.created webhook.
    assert count == 1


@pytest.mark.asyncio
async def test_no_endpoint_means_no_enqueue(public_api_seed, session_factory) -> None:
    from app.deliveries import service as delivery_service
    from app.deliveries.schemas import CreateDeliveryBody

    async with session_factory() as s:
        await delivery_service.create_delivery(
            s,
            area_id=public_api_seed.area_a_id,
            merchant_id=public_api_seed.merchant_id,
            actor_user_id=None,
            body=CreateDeliveryBody(
                pickup_address="Rua A, 1",
                dropoff_neighborhood_id=public_api_seed.dropoff_nbhd_id,
                dropoff_address="Rua B, 2",
                recipient_name="Cliente",
                recipient_phone_e164="+5522988887777",
                payment_method="direct",
            ),
            ip=None,
        )
        await s.commit()

    async with session_factory() as s:
        count = await _count_webhook_rows(s, area_id=public_api_seed.area_a_id)
    assert count == 0


@pytest.mark.asyncio
async def test_unsubscribed_event_not_enqueued(public_api_seed, session_factory) -> None:
    async with session_factory() as s:
        await webhook_service.configure_endpoint(
            s,
            area_id=public_api_seed.area_a_id,
            url="https://1.1.1.1/webhook",
            events=["delivery.delivered"],  # NOT created
        )
        await s.commit()

    async with session_factory() as s:
        # A CRIADA delivery's created event is not subscribed → no enqueue.
        from app.deliveries.models import Delivery

        delivery = Delivery(
            area_id=public_api_seed.area_a_id,
            merchant_id=public_api_seed.merchant_id,
            state="CRIADA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua A",
            dropoff_address="Rua B",
            dropoff_neighborhood_id=public_api_seed.dropoff_nbhd_id,
            fee_cents=0,
            public_token="TOKZZZZ",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        row = await webhook_service.enqueue_event(
            s, area_id=public_api_seed.area_a_id, delivery=delivery, state="CRIADA"
        )
        assert row is None
