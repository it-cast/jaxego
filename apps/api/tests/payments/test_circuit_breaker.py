"""Circuit breaker: PaymentPort down → card/pix returns a handled error; direct OK.

REQ-034. When the payment gateway is unavailable, creating a card/pix delivery
raises a handled error (not a 500), while a `direct` delivery still succeeds.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_card_charge_when_gateway_down_raises_handled(payments_seed, session_factory) -> None:
    from app.payments.errors import PaymentGatewayError
    from app.payments.safe2pay_stub import PaymentStubAdapter
    from app.payments.service import PaymentService

    down = PaymentStubAdapter(scenario="down")
    async with session_factory() as s:
        svc = PaymentService(s, payment=down)
        with pytest.raises(PaymentGatewayError):
            await svc.charge_delivery(
                area_id=payments_seed.area_a_id,
                delivery_id=1,
                corrida_cents=1000,
                taxa_cents=200,
                courier_recipient="recip_courier_1",
                method="card",
                customer_name="Loja",
                customer_document="12345678000190",
                customer_email="loja@example.com",
            )


@pytest.mark.asyncio
async def test_direct_delivery_unaffected_by_gateway(payments_seed, session_factory) -> None:
    """A `direct` delivery never touches PaymentPort, so a gateway outage is moot."""
    from app.deliveries.schemas import CreateDeliveryBody
    from app.deliveries.service import create_delivery

    async with session_factory() as s:
        body = CreateDeliveryBody(
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua A, 1",
            dropoff_address="Rua B, 2",
            dropoff_neighborhood_id=payments_seed.dropoff_nbhd_id,
            recipient_name="Cliente",
            recipient_phone_e164="+5522999990009",
        )
        resp = await create_delivery(
            s,
            area_id=payments_seed.area_a_id,
            merchant_id=payments_seed.merchant_id,
            actor_user_id=payments_seed.owner_user_id,
            body=body,
            ip=None,
        )
        await s.commit()
        assert resp.state == "CRIADA"
