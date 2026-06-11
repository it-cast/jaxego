"""Outbound webhook payload — PII minimisation BY STATE (RN-013 / TH-09 / D-08).

The webhook goes to a THIRD PARTY (the integrator), so the payload carries the
MINIMUM: the event, the `public_token` + `reference_number` (the handles the
integrator already knows), the state, and the dropoff NEIGHBOURHOOD — never the
recipient phone, never the recipient CPF, and the FULL dropoff address only AFTER
COLETADA (the same boundary the public tracker uses — `serialize_public`). The
serializer returns a plain dict whose KEYS are asserted by the PII test; adding a
forbidden key (recipient_phone, recipient_cpf, …) breaks the test.
"""

from __future__ import annotations

# Full dropoff address is revealed once the courier has collected (RN-013) — same
# boundary as the public tracker.
_ADDRESS_REVEALED_STATES = frozenset({"COLETADA", "ENTREGUE", "FINALIZADA"})

# delivery.state → public event type (D-08). RECUSADA_NO_DESTINO folds into canceled.
STATE_TO_EVENT = {
    "CRIADA": "delivery.created",
    "ACEITA": "delivery.accepted",
    "COLETADA": "delivery.collected",
    "ENTREGUE": "delivery.delivered",
    "FINALIZADA": "delivery.finalized",
    "CANCELADA": "delivery.canceled",
    "RECUSADA_NO_DESTINO": "delivery.canceled",
}


def event_for_state(state: str) -> str | None:
    """Map a delivery state to its public webhook event, or None if not surfaced."""
    return STATE_TO_EVENT.get(state)


def serialize_webhook(
    *,
    event_id: str,
    event_type: str,
    occurred_at: str,
    public_token: str,
    reference_number: str | None,
    state: str,
    dropoff_neighborhood_id: int,
    dropoff_address: str | None,
    dropoff_number: str | None,
    dropoff_complement: str | None,
) -> dict[str, object]:
    """Minimised webhook payload (RN-013 / TH-09). NEVER recipient phone/CPF."""
    data: dict[str, object] = {
        "public_token": public_token,
        "reference_number": reference_number,
        "state": state,
    }
    # Full dropoff address only after pickup; else neighbourhood only (RN-013).
    if state in _ADDRESS_REVEALED_STATES:
        data["dropoff"] = {
            "address": dropoff_address,
            "number": dropoff_number,
            "complement": dropoff_complement,
            "neighborhood_id": dropoff_neighborhood_id,
        }
    else:
        data["dropoff"] = {"neighborhood_id": dropoff_neighborhood_id}

    return {
        "id": event_id,
        "type": event_type,
        "occurred_at": occurred_at,
        "data": data,
    }
