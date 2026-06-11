"""PaymentService — domain orchestration over a PaymentPort (never the impl).

The service depends on the injected `PaymentPort` (the factory wires the Stub in
dev/test, the real adapter otherwise — D-09), never on a concrete Safe2Pay class. T-03
ships the base: the constructor + the idempotent charge-record helper. T-06 adds
`charge_delivery` (split + escrow hold), `refund_charge` (RN-004, area-scoped) and the
circuit-breaker wiring into delivery creation.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.payments import repo
from app.payments.models import PlatformCharge
from app.payments.port import PaymentPort


class PaymentService:
    """Orchestrates charges/escrow/refunds behind a PaymentPort (D-09)."""

    def __init__(self, session: AsyncSession, *, payment: PaymentPort) -> None:
        self._session = session
        self._payment = payment

    async def _record(
        self,
        *,
        area_id: int,
        idempotency_key: str,
        transaction_id: str | None,
        amount_cents: int,
        method: str,
        kind: str,
        status: str,
        subscription_id: int | None = None,
        delivery_id: int | None = None,
        due_at: datetime | None = None,
    ) -> PlatformCharge:
        """Idempotently persist a charge (TH-D) — delegates to the repo."""
        return await repo.record_charge(
            self._session,
            area_id=area_id,
            idempotency_key=idempotency_key,
            transaction_id=transaction_id,
            amount_cents=amount_cents,
            method=method,
            kind=kind,
            status=status,
            subscription_id=subscription_id,
            delivery_id=delivery_id,
            due_at=due_at,
        )
