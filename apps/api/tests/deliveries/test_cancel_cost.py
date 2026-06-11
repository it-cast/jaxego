"""RN-004 cancellation cost by state (T-04) — recorded, not charged here.

`cancellation_cost_cents` is a pure function: 0 pre-acceptance, 50% accepted, 100% +
return% after pickup. The charge itself is the Phase 11 invoice — here we pin the
computation and that `cancel_delivery` records it on the delivery.
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery
from app.deliveries.service import cancellation_cost_cents


def _delivery(state: str, estimate: int = 1000) -> Delivery:
    return Delivery(
        area_id=1,
        merchant_id=1,
        dropoff_neighborhood_id=1,
        state=state,
        pickup_address="a",
        dropoff_address="b",
        estimate_max_cents=estimate,
        fee_cents=0,
        items_quantity=1,
        public_token="X" * 26,
        origin="manual",
    )


def test_criada_costs_zero() -> None:
    assert cancellation_cost_cents(_delivery("CRIADA"), return_pct=20) == 0


def test_aceita_costs_50pct() -> None:
    assert cancellation_cost_cents(_delivery("ACEITA", 1000), return_pct=20) == 500


def test_coletada_costs_100pct_plus_return() -> None:
    # 1000 + 20% return = 1200.
    assert cancellation_cost_cents(_delivery("COLETADA", 1000), return_pct=20) == 1200


def test_coletada_zero_return() -> None:
    assert cancellation_cost_cents(_delivery("COLETADA", 1000), return_pct=0) == 1000


def test_unpriced_estimate_costs_zero() -> None:
    d = _delivery("ACEITA")
    d.estimate_max_cents = None
    assert cancellation_cost_cents(d, return_pct=20) == 0


def test_terminal_states_cost_zero() -> None:
    for state in ("ENTREGUE", "FINALIZADA", "CANCELADA", "RECUSADA_NO_DESTINO"):
        assert cancellation_cost_cents(_delivery(state, 1000), return_pct=50) == 0


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
        assert cancelled.cancel_cost_cents == 0  # CRIADA → free (RN-004)
