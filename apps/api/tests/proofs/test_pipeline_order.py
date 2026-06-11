"""The proof pipeline reads GPS BEFORE it strips (Pitfall 1) — the central invariant.

`test_exif_read_before_reprocess` patches BOTH `extract_gps_from_raw` and
`reprocess_to_webp` to append to a shared call log; the assertion is that EXIF
extraction is recorded STRICTLY before the strip. If the order ever regresses (the
KYC bug: strip first → GPS gone → every proof low_confidence), this fails.

The functional tests drive the whole pipeline through the StorageStub: an in-radius
photo → COLETADA + geofence_ok; an out-of-radius photo → OutOfGeofenceError with a
rising attempt counter; the 3rd failure → low_confidence + transition still happens
(CTA destrava, não trava para sempre — RN-005 / ADR-008).
"""

from __future__ import annotations

import pytest
from app.deliveries.models import Delivery
from app.proofs.service import OutOfGeofenceError, submit_photo_proof
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.proofs.conftest import (
    FAR_LAT,
    FAR_LNG,
    NEAR_LAT,
    NEAR_LNG,
    ProofSeed,
    make_jpeg_with_gps,
)


async def _upload(storage, key: str, raw: bytes) -> None:
    await storage.put_bytes(key, raw, content_type="image/jpeg")


@pytest.mark.asyncio
async def test_exif_read_before_reprocess(
    session_factory: async_sessionmaker[AsyncSession],
    proof_seed: ProofSeed,
    storage_stub,
    monkeypatch,
) -> None:
    """EXIF extraction is recorded strictly BEFORE the reprocess/strip."""
    calls: list[str] = []

    import app.proofs.service as svc

    real_exif = svc.extract_gps_from_raw

    def spy_exif(raw: bytes):
        calls.append("exif")
        return real_exif(raw)

    def spy_reprocess(raw: bytes):
        calls.append("reprocess")
        return b"RIFF0000WEBPxx", "deadbeef"

    monkeypatch.setattr(svc, "extract_gps_from_raw", spy_exif)
    monkeypatch.setattr(svc, "reprocess_to_webp", spy_reprocess)

    key = "proofs/x/raw.jpg"
    await _upload(storage_stub, key, make_jpeg_with_gps(NEAR_LAT, NEAR_LNG))

    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="pickup",
            storage_key=key,
            client_lat=NEAR_LAT,
            client_lng=NEAR_LNG,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()

    assert calls == ["exif", "reprocess"], calls
    assert calls.index("exif") < calls.index("reprocess")


@pytest.mark.asyncio
async def test_in_radius_pickup_transitions_to_coletada(
    session_factory: async_sessionmaker[AsyncSession],
    proof_seed: ProofSeed,
    storage_stub,
) -> None:
    key = "proofs/x/ok.jpg"
    await _upload(storage_stub, key, make_jpeg_with_gps(NEAR_LAT, NEAR_LNG))
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        proof = await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="pickup",
            storage_key=key,
            client_lat=NEAR_LAT,
            client_lng=NEAR_LNG,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()
        assert proof.geofence_ok is True
        assert proof.low_confidence is False
        assert proof.storage_key == f"{key}.webp"
        refreshed = await s.get(Delivery, proof_seed.delivery_id)
        assert refreshed.state == "COLETADA"


@pytest.mark.asyncio
async def test_out_of_radius_rejected_then_low_confidence(
    session_factory: async_sessionmaker[AsyncSession],
    proof_seed: ProofSeed,
    storage_stub,
) -> None:
    """1st/2nd out-of-radius → 422 with counter; 3rd → low_confidence + COLETADA."""
    key = "proofs/x/far.jpg"
    await _upload(storage_stub, key, make_jpeg_with_gps(FAR_LAT, FAR_LNG))

    for attempt in (1, 2):
        async with session_factory() as s:
            delivery = await s.get(Delivery, proof_seed.delivery_id)
            with pytest.raises(OutOfGeofenceError) as exc:
                await submit_photo_proof(
                    s,
                    storage_stub,
                    delivery=delivery,
                    actor_user_id=proof_seed.courier_user_id,
                    proof_kind="pickup",
                    storage_key=key,
                    client_lat=FAR_LAT,
                    client_lng=FAR_LNG,
                    refusal_reason=None,
                    ip=None,
                )
            await s.commit()
            assert exc.value.failed_attempts == attempt
            assert (await s.get(Delivery, proof_seed.delivery_id)).state == "ACEITA"

    # 3rd attempt → low_confidence, the CTA unlocks, transition proceeds.
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        proof = await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="pickup",
            storage_key=key,
            client_lat=FAR_LAT,
            client_lng=FAR_LNG,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()
        assert proof.low_confidence is True
        assert proof.geofence_ok is False
        assert (await s.get(Delivery, proof_seed.delivery_id)).state == "COLETADA"


@pytest.mark.asyncio
async def test_missing_gps_rejected(
    session_factory: async_sessionmaker[AsyncSession],
    proof_seed: ProofSeed,
    storage_stub,
) -> None:
    """No client GPS and no EXIF → gps_missing (E1, actionable)."""
    from app.proofs.service import GpsMissingError

    from tests.proofs.conftest import make_jpeg_no_gps

    key = "proofs/x/nogps.jpg"
    await _upload(storage_stub, key, make_jpeg_no_gps())
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        with pytest.raises(GpsMissingError):
            await submit_photo_proof(
                s,
                storage_stub,
                delivery=delivery,
                actor_user_id=proof_seed.courier_user_id,
                proof_kind="pickup",
                storage_key=key,
                client_lat=None,
                client_lng=None,
                refusal_reason=None,
                ip=None,
            )


@pytest.mark.asyncio
async def test_exif_used_when_client_gps_absent(
    session_factory: async_sessionmaker[AsyncSession],
    proof_seed: ProofSeed,
    storage_stub,
) -> None:
    """EXIF GPS is the fallback when the client sends no {lat,lng}."""
    key = "proofs/x/exifonly.jpg"
    await _upload(storage_stub, key, make_jpeg_with_gps(NEAR_LAT, NEAR_LNG))
    async with session_factory() as s:
        delivery = await s.get(Delivery, proof_seed.delivery_id)
        proof = await submit_photo_proof(
            s,
            storage_stub,
            delivery=delivery,
            actor_user_id=proof_seed.courier_user_id,
            proof_kind="pickup",
            storage_key=key,
            client_lat=None,
            client_lng=None,
            refusal_reason=None,
            ip=None,
        )
        await s.commit()
        assert proof.geofence_ok is True
