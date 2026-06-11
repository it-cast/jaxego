"""F-06 transitions + RN-013 reveal (T-04).

The proof pipeline drives COLETADA/ENTREGUE/RECUSADA via the Phase 7 `transition()`
(append-only, 422 on invalid). Here we assert: a pickup proof reveals the dropoff
address (RN-013 `dropoff_revealed`), a delivery proof from COLETADA → ENTREGUE, a
refusal proof → RECUSADA_NO_DESTINO with the reason, and an invalid order (delivery
proof while still ACEITA) → 422 from the state machine.
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery
from app.deliveries.service import dropoff_revealed
from app.deliveries.state_machine import InvalidTransitionError
from app.proofs.service import submit_photo_proof
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.proofs.conftest import NEAR_LAT, NEAR_LNG, ProofSeed, make_jpeg_with_gps


async def _upload(storage, key: str) -> None:
    await storage.put_bytes(key, make_jpeg_with_gps(NEAR_LAT, NEAR_LNG), content_type="image/jpeg")


def test_dropoff_revealed_by_state() -> None:
    assert dropoff_revealed("CRIADA") is False
    assert dropoff_revealed("ACEITA") is False
    assert dropoff_revealed("COLETADA") is True
    assert dropoff_revealed("ENTREGUE") is True
    assert dropoff_revealed("FINALIZADA") is True


@pytest.mark.asyncio
async def test_pickup_then_delivery_chain(
    session_factory: async_sessionmaker[AsyncSession], proof_seed: ProofSeed, storage_stub
) -> None:
    """ACEITA →(pickup)→ COLETADA →(delivery)→ ENTREGUE; address revealed at COLETADA."""
    await _upload(storage_stub, "proofs/p1.jpg")
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="pickup",
            storage_key="proofs/p1.jpg",
            client_lat=NEAR_LAT,
            client_lng=NEAR_LNG,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()
        assert delivery.state == "COLETADA"
        assert dropoff_revealed(delivery.state) is True

    await _upload(storage_stub, "proofs/p2.jpg")
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="delivery",
            storage_key="proofs/p2.jpg",
            client_lat=NEAR_LAT,
            client_lng=NEAR_LNG,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()
        assert delivery.state == "ENTREGUE"


@pytest.mark.asyncio
async def test_refusal_transitions_with_reason(
    session_factory: async_sessionmaker[AsyncSession], proof_seed: ProofSeed, storage_stub
) -> None:
    """A refusal proof from COLETADA → RECUSADA_NO_DESTINO with the reason recorded."""
    # First collect.
    await _upload(storage_stub, "proofs/c.jpg")
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="pickup",
            storage_key="proofs/c.jpg",
            client_lat=NEAR_LAT,
            client_lng=NEAR_LNG,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()
    # Then refuse at destination.
    await _upload(storage_stub, "proofs/r.jpg")
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        proof = await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="refusal",
            storage_key="proofs/r.jpg",
            client_lat=NEAR_LAT,
            client_lng=NEAR_LNG,
            refusal_reason="absent",
            ip=None,
        )
        await s.commit()
        assert delivery.state == "RECUSADA_NO_DESTINO"
        assert proof.refusal_reason == "absent"


@pytest.mark.asyncio
async def test_invalid_order_delivery_while_aceita_raises_422(
    session_factory: async_sessionmaker[AsyncSession], proof_seed: ProofSeed, storage_stub
) -> None:
    """A delivery proof while still ACEITA (no pickup) → 422 from the machine."""
    await _upload(storage_stub, "proofs/bad.jpg")
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        with pytest.raises(InvalidTransitionError):
            await submit_photo_proof(
                s,
                storage_stub,
                delivery=delivery,
                actor_user_id=proof_seed.courier_user_id,
                proof_kind="delivery",  # ACEITA → ENTREGUE is not allowed
                storage_key="proofs/bad.jpg",
                client_lat=NEAR_LAT,
                client_lng=NEAR_LNG,
                refusal_reason=None,
                ip=None,
            )
