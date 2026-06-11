"""Payment error hierarchy (RFC-7807 envelope via AppError).

`PaymentGatewayError` is raised whenever Safe2Pay signals a business error
(`HasError: true`, even on HTTP 200 — skill A2) or is unavailable (circuit breaker,
REQ-034). It carries an optional `code` (the Safe2Pay `ErrorCode`) but NEVER any
card/token payload (A09). A gateway failure is a handled 502 — the caller decides
whether to surface it (card/pix) or degrade (the `direct` flow is untouched).
"""

from __future__ import annotations

from app.core.exceptions import AppError


class PaymentGatewayError(AppError):
    """Safe2Pay business error / unavailability. NEVER carries card/token (A09)."""

    status_code = 502
    code = "payment_gateway_error"

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        super().__init__(message or "Pagamento indisponível no momento.", code=code)
