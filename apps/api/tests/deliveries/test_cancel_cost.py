"""Cancellation cost by state (T-04) — CORRECAO-249/250.

`cancellation_cost_cents` is always 0: cancelling is only possible pre-acceptance
(the state machine no longer allows CANCELADA from ACEITA/COLETADA — the old
50%/100% RN-004 cost was never wired to a real charge or courier payout, so
allowing it just left PIX money stuck with nobody compensated).
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery
from app.deliveries.service import cancellation_cost_cents


def _delivery(state: str, price: int = 1000) -> Delivery:
    return Delivery(
        area_id=1,
        merchant_id=1,
        dropoff_neighborhood_id=1,
        state=state,
        pickup_address="a",
        dropoff_address="b",
        price_cents=price,
        fee_cents=0,
        items_quantity=1,
        public_token="X" * 26,
        origin="manual",
    )


@pytest.mark.parametrize(
    "state",
    [
        "AGENDADA",
        "AGUARDANDO_PAGAMENTO",
        "CRIADA",
        "SEM_RESPOSTA",
        "ACEITA",
        "COLETADA",
        "ENTREGUE",
        "FINALIZADA",
        "CANCELADA",
        "RECUSADA_NO_DESTINO",
    ],
)
def test_cancellation_is_always_free(state: str) -> None:
    assert cancellation_cost_cents(_delivery(state, 1000), return_pct=20) == 0


@pytest.mark.asyncio
async def test_cancel_records_cost_on_delivery(session_factory, delivery_seed) -> None:
    """cancel_delivery on a CRIADA delivery records a 0 cost (free pre-acceptance)."""
    from app.deliveries import service
    from app.deliveries.schemas import CreateDeliveryBody, PaymentMethod

    body = CreateDeliveryBody(
        pickup_address="Rua do Comércio, 100",
        dropoff_neighborhood_id=delivery_seed.dropoff_nbhd_id,
        dropoff_address="Rua das Flores, 200",
        recipient_name="Cliente",
        recipient_phone_e164="+5522988887777",
        payment_method=PaymentMethod.direct,
    )
    async with session_factory() as s:
        created = await service.create_delivery(
            s,
            area_id=delivery_seed.area_a_id,
            merchant_id=delivery_seed.merchant_id,
            actor_user_id=delivery_seed.owner_user_id,
            body=body,
            ip=None,
        )
        await s.commit()
    async with session_factory() as s:
        cancelled = await service.cancel_delivery(
            s,
            area_id=delivery_seed.area_a_id,
            merchant_id=delivery_seed.merchant_id,
            actor_user_id=delivery_seed.owner_user_id,
            delivery_id=created.delivery_id,
            reason="store changed mind",
            ip=None,
        )
        await s.commit()
        assert cancelled.state == "CANCELADA"
        assert cancelled.cancel_cost_cents == 0
