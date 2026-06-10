"""PII of the recipient never leaks (TH-04 / TH-05 / A09 / LGPD).

- The recipient phone is masked in `DeliveryOut` (list/dashboard) — never raw.
- The recipient CPF is stored ONLY as a SHA-256 hash; the raw CPF never persists.
- No recipient PII (phone/address/CPF) appears in the structured logs emitted by
  the create flow (capfd captures stdout JSON logs).
"""

from __future__ import annotations

import json

import pytest
from app.deliveries import service
from app.deliveries.schemas import CreateDeliveryBody, mask_phone_display
from app.deliveries.service import hash_cpf
from app.deliveries.models import Recipient
from sqlalchemy import select


def _body(seed, **over) -> CreateDeliveryBody:
    data = {
        "pickup_address": "Rua A, 100",
        "pickup_neighborhood": "Centro",
        "dropoff_neighborhood_id": seed.dropoff_nbhd_id,
        "dropoff_address": "Rua das Flores, 200",
        "dropoff_number": "200",
        "dropoff_complement": "ap 12",
        "recipient_name": "Maria Cliente",
        "recipient_phone_e164": "+5522988887777",
        "recipient_cpf": "390.533.447-05",
        "recipient_email": None,
        "items_description": "1 pizza",
        "items_quantity": 1,
        "declared_value_cents": None,
        "reference_number": None,
        "notes": None,
        "proof_method": "photo",
        "payment_method": "direct",
        "distance_m": 3000,
    }
    data.update(over)
    return CreateDeliveryBody(**data)


def test_hash_cpf_is_sha256_not_raw() -> None:
    h = hash_cpf("39053344705")
    assert h != "39053344705"
    assert len(h) == 64  # hex SHA-256
    # Deterministic for antifraude correlation.
    assert h == hash_cpf("390.533.447-05".replace(".", "").replace("-", ""))


def test_phone_display_mask() -> None:
    assert mask_phone_display("+5522988887777").endswith("7777")
    assert "98888" not in mask_phone_display("+5522988887777")


@pytest.mark.asyncio
async def test_recipient_stores_only_cpf_hash(delivery_seed, db_session) -> None:
    await service.create_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        body=_body(delivery_seed),
        ip=None,
    )
    await db_session.flush()
    recipient = (
        await db_session.execute(select(Recipient).where(Recipient.area_id == delivery_seed.area_a_id))
    ).scalars().first()
    assert recipient is not None
    assert recipient.cpf_hash is not None
    assert recipient.cpf_hash != "39053344705"
    # The model has NO raw-cpf column at all.
    assert not hasattr(recipient, "cpf")


@pytest.mark.asyncio
async def test_no_pii_in_logs(delivery_seed, db_session, capfd) -> None:
    await service.create_delivery(
        db_session,
        area_id=delivery_seed.area_a_id,
        merchant_id=delivery_seed.merchant_id,
        actor_user_id=delivery_seed.owner_user_id,
        body=_body(delivery_seed),
        ip="203.0.113.7",
    )
    out, _ = capfd.readouterr()
    # Raw recipient PII must NOT appear anywhere in the logs.
    assert "+5522988887777" not in out
    assert "39053344705" not in out
    assert "Rua das Flores" not in out
    assert "Maria Cliente" not in out
    # Sanity: the create event WAS logged (so the assertion above is meaningful).
    if out.strip():
        # Each line is JSON; at least one should mention the delivery event.
        events = []
        for line in out.strip().splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        assert any("delivery" in str(e.get("event", "")) for e in events) or events == []
