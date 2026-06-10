"""Courier + document state machines (D-04/D-08). Invalid transition → 422.

Mirrors `merchants/state_machine.py`: explicit transition maps, an
`assert_transition` that raises a 422 AppError, and the service records each
transition in `audit_log` (RN-012). Two machines: the courier lifecycle and the
per-document KYC item lifecycle. The per-document machine is what makes E4 work —
a `rejected` document can go back to `pending_upload` (re-upload just that item)
WITHOUT touching any other document's status.
"""

from __future__ import annotations

from app.core.exceptions import AppError

COURIER_TRANSITIONS: dict[str, set[str]] = {
    "pending_kyc": {"active", "banned"},
    "active": {"suspended", "banned"},
    "suspended": {"active", "banned"},
    "banned": set(),
}

DOCUMENT_TRANSITIONS: dict[str, set[str]] = {
    "pending_upload": {"pending"},  # upload + reprocess OK → enters the queue
    "pending": {"approved", "rejected"},  # admin item-a-item decision
    "approved": {"expired", "rejected"},  # expiry (job) or revocation
    "rejected": {"pending_upload"},  # re-upload ONLY this item (E4)
    "expired": {"pending_upload"},  # re-upload after expiry
}


class InvalidTransitionError(AppError):
    """An illegal courier/document status transition was attempted (422)."""

    status_code = 422
    code = "invalid_transition"

    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Transição de status inválida: {current} → {target}.")


def assert_courier_transition(current: str, target: str) -> None:
    """Raise InvalidTransitionError unless the courier current→target is allowed."""
    if target not in COURIER_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)


def assert_document_transition(current: str, target: str) -> None:
    """Raise InvalidTransitionError unless the document current→target is allowed."""
    if target not in DOCUMENT_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)
