"""Public tracking serializer — PII minimisation BY STATE (RN-013 / RN-022 / TH-3).

The public tracker has NO auth (token-only), so the payload must carry the MINIMUM:
state, timeline, ETA, and an APPROXIMATE courier position. The rules are structural,
not a forgettable filter:

- **Dropoff address (RN-013):** full address ONLY after COLETADA (COLETADA/ENTREGUE/
  FINALIZADA); before that, neighbourhood id only.
- **Courier PII (TH-3):** NEVER name/phone/CPF in the public payload — only a
  vehicle type at most. The courier is anonymous on the public side.
- **Recipient phone (RN-022):** phones are reachable to the parties ONLY in the
  ACEITA→FINALIZADA window; the PUBLIC payload never emits the recipient phone at all
  (a public link is not a party). `phone_window_open(state)` is the predicate the
  authenticated store/courier surfaces use (tested here for RN-022).
- **Position:** the last sample, exposed only while ACEITA/COLETADA (the moving
  window); FINALIZADA/terminal → no position. Approximate (rounded) — never precise
  lat/long in text (trust-safety).

The serializer returns a plain dict whose KEYS are asserted by the PII test — adding
a forbidden key (recipient_phone, courier_name, …) breaks the test.
"""

from __future__ import annotations

# Dropoff full address is revealed once the courier has collected (RN-013).
_ADDRESS_REVEALED_STATES = frozenset({"COLETADA", "ENTREGUE", "FINALIZADA"})
# The moving window where a courier position makes sense.
_POSITION_STATES = frozenset({"ACEITA", "COLETADA"})
# RN-022: phones reachable to the PARTIES only in this window (not the public link).
_PHONE_WINDOW_STATES = frozenset({"ACEITA", "COLETADA", "ENTREGUE"})

# Position is rounded to ~110 m (3 decimals) — approximate, never precise (trust-safety).
_POSITION_PRECISION = 3


def phone_window_open(state: str) -> bool:
    """True if telefones are reachable to the parties in this state (RN-022).

    Window = ACEITA→FINALIZADA (the active delivery). FINALIZADA itself closes the
    window (the run is done). Used by the authenticated store/courier surfaces; the
    PUBLIC payload never emits a phone regardless.
    """
    return state in _PHONE_WINDOW_STATES


def serialize_public(
    *,
    state: str,
    timeline: list[dict[str, object]],
    eta_seconds: int | None,
    dropoff_neighborhood_id: int,
    dropoff_address: str | None,
    dropoff_number: str | None,
    dropoff_complement: str | None,
    courier_vehicle_type: str | None,
    last_lat: float | None,
    last_lng: float | None,
) -> dict[str, object]:
    """Minimised public tracking payload (RN-013 / RN-022 / TH-3)."""
    out: dict[str, object] = {
        "state": state,
        "timeline": timeline,
        "eta_seconds": eta_seconds,
    }

    # RN-013: full dropoff address only after pickup; else neighbourhood only.
    if state in _ADDRESS_REVEALED_STATES:
        out["dropoff"] = {
            "address": dropoff_address,
            "number": dropoff_number,
            "complement": dropoff_complement,
            "neighborhood_id": dropoff_neighborhood_id,
        }
    else:
        out["dropoff"] = {"neighborhood_id": dropoff_neighborhood_id}

    # Courier is anonymous publicly — vehicle type at most (TH-3). No name/phone/cpf.
    out["courier"] = {"vehicle_type": courier_vehicle_type} if courier_vehicle_type else None

    # Approximate position only while moving (ACEITA/COLETADA).
    if state in _POSITION_STATES and last_lat is not None and last_lng is not None:
        out["courier_position"] = {
            "lat": round(last_lat, _POSITION_PRECISION),
            "lng": round(last_lng, _POSITION_PRECISION),
        }
    else:
        out["courier_position"] = None

    return out
