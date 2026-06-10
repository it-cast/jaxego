"""Delivery state machine (RN-019 / D-03). Invalid transition → 422.

Mirrors `couriers/state_machine.py`: explicit transition map (`dict[str, set[str]]`),
an `assert_delivery_transition` that raises a 422 AppError, and the service records
each transition in `delivery_state_transitions` (append-only — RN-012). The WHOLE
machine (7 states) is defined NOW even though only CRIADA and CANCELADA are
reachable in Phase 7; ACEITA+ are exercised in Phases 8/9. A new state requires an
ADR (D-03).

Transition set confirmed against fluxos.md F-03 (create) / F-05 (dispatch+accept) /
F-06 (delivery+refusal):
  - CRIADA → ACEITA (Phase 8 accept) | CANCELADA (store cancels pre-acceptance, RN-004 zero cost)
  - ACEITA → COLETADA (Phase 9 pickup) | CANCELADA (post-acceptance cancel, RN-004 50%)
  - COLETADA → ENTREGUE | RECUSADA_NO_DESTINO (F-06 refusal) | CANCELADA
  - ENTREGUE → FINALIZADA (Phase 9 settle job)
  - RECUSADA_NO_DESTINO → FINALIZADA (settle with refusal)
  - CANCELADA / FINALIZADA → terminal (no exits)
"""

from __future__ import annotations

from app.core.exceptions import AppError

# The 7 canonical states (RN-019 / D-03).
DELIVERY_STATES = (
    "CRIADA",
    "ACEITA",
    "COLETADA",
    "ENTREGUE",
    "RECUSADA_NO_DESTINO",
    "CANCELADA",
    "FINALIZADA",
)

# Valid transitions (RN-019). Defined in full now; only CRIADA/CANCELADA are
# exercised in Phase 7, the rest are covered by tests and enabled in Phases 8/9.
DELIVERY_TRANSITIONS: dict[str, set[str]] = {
    "CRIADA": {"ACEITA", "CANCELADA"},
    "ACEITA": {"COLETADA", "CANCELADA"},
    "COLETADA": {"ENTREGUE", "RECUSADA_NO_DESTINO", "CANCELADA"},
    "ENTREGUE": {"FINALIZADA"},
    "RECUSADA_NO_DESTINO": {"FINALIZADA"},
    "CANCELADA": set(),  # terminal
    "FINALIZADA": set(),  # terminal
}


class InvalidTransitionError(AppError):
    """An illegal delivery state transition was attempted (422 — TH-01)."""

    status_code = 422
    code = "invalid_transition"

    def __init__(self, current: str | None, target: str) -> None:
        super().__init__(f"Transição de status inválida: {current} → {target}.")


def assert_delivery_transition(current: str, target: str) -> None:
    """Raise InvalidTransitionError unless current→target is allowed (RN-019)."""
    if target not in DELIVERY_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)
