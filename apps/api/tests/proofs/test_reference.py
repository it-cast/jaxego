"""Reference-number proof (E4 / REQ-028): match → ENTREGUE; 3 wrong → locked → manual.

The delivery must be COLETADA before a delivery proof is valid (the machine). We
collect first, then: a correct number → ENTREGUE; wrong numbers raise a rising counter
and the 3rd locks; the store then releases manually (recorded reason `manual_release`).
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery, DeliveryStateTransition
from app.proofs.reference import (
    ReferenceLockedError,
    ReferenceMismatchError,
    manual_release,
    submit_reference_proof,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.proofs.conftest import NEAR_LAT, NEAR_LNG, ProofSeed, make_jpeg_with_gps


async def _collect(session_factory, proof_seed: ProofSeed, storage_stub) -> None:
    """Drive the delivery to COLETADA via a valid pickup proof."""
    from app.proofs.service import submit_photo_proof

    await storage_stub.put_bytes(
        "proofs/c.jpg", make_jpeg_with_gps(NEAR_LAT, NEAR_LNG), content_type="image/jpeg"
    )
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


@pytest.mark.asyncio
async def test_correct_reference_delivers(
    session_factory: async_sessionmaker[AsyncSession], proof_seed: ProofSeed, storage_stub
) -> None:
    await _collect(session_factory, proof_seed, storage_stub)
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        result = await submit_reference_proof(
            s,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            reference_number="a1b2c3",  # case-insensitive match of "A1B2C3"
            ip=None,
        )
        await s.commit()
        assert result.state == "ENTREGUE"
        assert (await s.get(Delivery, proof_seed.delivery_id)).state == "ENTREGUE"


@pytest.mark.asyncio
async def test_three_wrong_locks_then_manual_release(
    session_factory: async_sessionmaker[AsyncSession], proof_seed: ProofSeed, storage_stub
) -> None:
    await _collect(session_factory, proof_seed, storage_stub)

    # 1st + 2nd wrong → mismatch with a rising counter.
    for attempt in (1, 2):
        async with session_factory() as s:
            delivery = await s.get(Delivery, proof_seed.delivery_id)
            with pytest.raises(ReferenceMismatchError) as exc:
                await submit_reference_proof(
                    s,
                    delivery=delivery,
                    actor_user_id=proof_seed.courier_user_id,
                    reference_number="WRONG",
                    ip=None,
                )
            await s.commit()
            assert exc.value.attempts == attempt
            assert (await s.get(Delivery, proof_seed.delivery_id)).state == "COLETADA"

    # 3rd wrong → locked.
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        with pytest.raises(ReferenceLockedError):
            await submit_reference_proof(
                s,
                delivery=delivery,
                actor_user_id=proof_seed.courier_user_id,
                reference_number="WRONG",
                ip=None,
            )
        await s.commit()

    # Further attempts stay locked (even with the correct number).
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        with pytest.raises(ReferenceLockedError):
            await submit_reference_proof(
                s,
                delivery=delivery,
                actor_user_id=proof_seed.courier_user_id,
                reference_number="A1B2C3",
                ip=None,
            )
        await s.commit()

    # Store releases manually → ENTREGUE, reason recorded (auditable).
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        await manual_release(s, delivery=delivery, actor_user_id=None, ip=None)
        await s.commit()
        assert (await s.get(Delivery, proof_seed.delivery_id)).state == "ENTREGUE"
        reasons = (
            (
                await s.execute(
                    select(DeliveryStateTransition.reason).where(
                        DeliveryStateTransition.delivery_id == proof_seed.delivery_id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert "manual_release" in reasons
