"""Dispatch error types (RFC-7807 envelope via AppError).

`OfferAlreadyTakenError` (409) — the second concurrent accept lost the race
(F-05 E3). It is a NON-EVENT, not a cancel: ZERO penalty for the courier who only
lost the network race (Pitfall 1). `NotOfferTargetError` (404) — the courier is
not the target of the current offer (A01 / TH-4): we return 404, never 403, so we
do not leak that an offer exists for someone else.
"""

from __future__ import annotations

from app.core.exceptions import AppError


class OfferAlreadyTakenError(AppError):
    """The offer was already accepted by someone else (409, F-05 E3, no penalty)."""

    status_code = 409
    code = "offer_already_taken"

    def __init__(self) -> None:
        super().__init__(
            "Essa entrega acabou de ser aceita por outro entregador. "
            "Sem problema — a próxima é sua."
        )


class NotOfferTargetError(AppError):
    """This courier is not the target of the current offer (404 — A01 / TH-4)."""

    status_code = 404
    code = "offer_not_found"

    def __init__(self) -> None:
        # 404, never 403 — do not leak that an offer exists for another courier.
        super().__init__("Oferta não encontrada.")
