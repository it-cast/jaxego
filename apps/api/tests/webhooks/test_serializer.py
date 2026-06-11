"""Webhook payload PII minimisation (T-06 / TH-09 / RN-013).

The outbound payload goes to a third party, so it must NEVER carry the recipient
phone or CPF, and the FULL dropoff address only after COLETADA. The test asserts
the KEY SET (a forbidden key would break it) and the address boundary by state.
"""

from __future__ import annotations

import json

from app.webhooks.serializer import event_for_state, serialize_webhook

_FORBIDDEN_SUBSTRINGS = ("phone", "cpf", "recipient_name", "+5522", "telefone")


def _serialize(state: str) -> dict:
    return serialize_webhook(
        event_id="01J0EVENTID0000000000000AB",
        event_type=event_for_state(state),
        occurred_at="2026-06-11T12:00:00+00:00",
        public_token="TOKEN123",
        reference_number="PEDIDO-42",
        state=state,
        dropoff_neighborhood_id=7,
        dropoff_address="Rua Secreta",
        dropoff_number="200",
        dropoff_complement="ap 3",
    )


def test_no_recipient_pii_in_any_state() -> None:
    for state in ("CRIADA", "ACEITA", "COLETADA", "ENTREGUE", "FINALIZADA", "CANCELADA"):
        blob = json.dumps(_serialize(state)).lower()
        for forbidden in _FORBIDDEN_SUBSTRINGS:
            assert forbidden not in blob, (state, forbidden)


def test_address_hidden_before_pickup() -> None:
    payload = _serialize("CRIADA")
    assert payload["data"]["dropoff"] == {"neighborhood_id": 7}
    assert "Rua Secreta" not in json.dumps(payload)


def test_address_revealed_after_pickup() -> None:
    payload = _serialize("COLETADA")
    assert payload["data"]["dropoff"]["address"] == "Rua Secreta"
    assert payload["data"]["dropoff"]["neighborhood_id"] == 7


def test_event_mapping_covers_states() -> None:
    assert event_for_state("CRIADA") == "delivery.created"
    assert event_for_state("CANCELADA") == "delivery.canceled"
    assert event_for_state("RECUSADA_NO_DESTINO") == "delivery.canceled"
    assert event_for_state("UNKNOWN") is None


def test_payload_carries_known_handles() -> None:
    payload = _serialize("CRIADA")
    assert payload["data"]["public_token"] == "TOKEN123"
    assert payload["data"]["reference_number"] == "PEDIDO-42"
    assert payload["type"] == "delivery.created"
    assert payload["id"] == "01J0EVENTID0000000000000AB"
