"""serialize_public minimises PII by state (RN-013 / TH-3) — pure-function tests.

The forbidden keys (courier_name/phone/cpf, recipient_phone) must NEVER appear in the
payload, and the full dropoff address must appear ONLY after COLETADA. These assert
the serializer directly (no DB) so the contract is pinned regardless of the endpoint.
"""

from __future__ import annotations

import json

from app.tracking.serializer import serialize_public

_FORBIDDEN_SUBSTRINGS = ("phone", "cpf", "recipient", "courier_name", "full_name")


def _serialize(state: str, *, with_loc: bool = True) -> dict:
    return serialize_public(
        state=state,
        timeline=[{"state": "CRIADA", "at": "2026-06-10T00:00:00+00:00"}],
        eta_seconds=600,
        dropoff_neighborhood_id=42,
        dropoff_address="Rua das Flores, 200",
        dropoff_number="200",
        dropoff_complement="ap 3",
        courier_vehicle_type="moto",
        last_lat=-21.5405 if with_loc else None,
        last_lng=-42.1805 if with_loc else None,
    )


def test_no_courier_pii_keys_any_state() -> None:
    for state in ("CRIADA", "ACEITA", "COLETADA", "ENTREGUE", "FINALIZADA"):
        blob = json.dumps(_serialize(state)).lower()
        for bad in _FORBIDDEN_SUBSTRINGS:
            assert bad not in blob, (state, bad)


def test_address_hidden_before_coletada() -> None:
    out = _serialize("ACEITA")
    dropoff = out["dropoff"]
    assert dropoff == {"neighborhood_id": 42}
    assert "Rua das Flores" not in json.dumps(out)


def test_address_revealed_after_coletada() -> None:
    for state in ("COLETADA", "ENTREGUE", "FINALIZADA"):
        out = _serialize(state)
        dropoff = out["dropoff"]
        assert dropoff["address"] == "Rua das Flores, 200"
        assert dropoff["number"] == "200"


def test_courier_only_vehicle_type() -> None:
    out = _serialize("COLETADA")
    assert out["courier"] == {"vehicle_type": "moto"}


def test_position_only_while_moving() -> None:
    assert _serialize("ACEITA")["courier_position"] is not None
    assert _serialize("COLETADA")["courier_position"] is not None
    # Terminal/non-moving states → no position.
    assert _serialize("ENTREGUE")["courier_position"] is None
    assert _serialize("FINALIZADA")["courier_position"] is None
    assert _serialize("CRIADA")["courier_position"] is None


def test_position_is_approximate_rounded() -> None:
    out = _serialize("COLETADA")
    pos = out["courier_position"]
    # 3-decimal rounding — never the precise sample.
    assert pos["lat"] == round(-21.5405, 3)
    assert pos["lng"] == round(-42.1805, 3)
