"""Merchant state machine (D-05). Explicit transitions; invalid → 422.

Every transition is validated here and (by the service) recorded in `audit_log`
(RN-012). [ASSUMED A8] suspended↔active is allowed; active→pending_* is not.
"""

from __future__ import annotations

from app.core.exceptions import AppError

MERCHANT_TRANSITIONS: dict[str, set[str]] = {
    "pending_payment": {"active", "suspended"},
    "pending_validation": {"active", "suspended"},
    "active": {"suspended"},
    "suspended": {"active"},
}


class InvalidTransitionError(AppError):
    """An illegal merchant status transition was attempted (422)."""

    status_code = 422
    code = "invalid_transition"

    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Transição de status inválida: {current} → {target}.")


def assert_transition(current: str, target: str) -> None:
    """Raise InvalidTransitionError unless current→target is allowed."""
    if target not in MERCHANT_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)
