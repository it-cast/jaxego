"""PaymentService — domain orchestration over a PaymentPort (never the impl).

The service depends on the injected `PaymentPort` (the factory wires the Stub in
dev/test, the real adapter otherwise — D-09), never on a concrete Safe2Pay class. T-03
ships the base: the constructor + the idempotent charge-record helper. T-06 adds
`charge_delivery` (split + escrow hold), `refund_charge` (RN-004, area-scoped) and the
circuit-breaker wiring into delivery creation.
"""

from __future__ import annotations

from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.payments import escrow, repo
from app.payments.fees import build_splits, refund_amount_cents
from app.payments.models import PlatformCharge
from app.payments.port import ChargeResult, Customer, PaymentPort

logger = structlog.get_logger("payments.service")


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

    # -----------------------------------------------------------------------
    # Delivery split charge (F-03 / TH-F) — the split is built in the backend.
    # -----------------------------------------------------------------------
    async def charge_delivery(
        self,
        *,
        area_id: int,
        delivery_id: int,
        corrida_cents: int,
        taxa_cents: int,
        courier_recipient: str,
        method: str,
        customer_name: str,
        customer_document: str,
        customer_email: str,
        courier_id: int | None = None,
        revenue_share_pct: int | None = None,
        hold_escrow: bool = False,
    ) -> ChargeResult:
        """Charge corrida+taxa with a split; record the charge (+ escrow hold).

        Raises `PaymentGatewayError` on refusal/outage — the caller (delivery creation)
        does NOT insert the delivery in that case (F-03 E3). The split sum is exact
        (TH-F). Idempotent by `Reference = dlv_{id}` (TH-D). `hold_escrow` creates the
        24h escrow hold for the courier's corrida (requires `courier_id`).
        """
        share = (
            revenue_share_pct
            if revenue_share_pct is not None
            else settings.revenue_share_default_pct
        )
        jaxego_recipient = settings.safe2pay_jaxego_recipient or "jaxego"
        splits = build_splits(
            corrida_cents=corrida_cents,
            taxa_cents=taxa_cents,
            courier_recipient=courier_recipient,
            jaxego_recipient=jaxego_recipient,
            revenue_share_pct=share,
        )
        amount = corrida_cents + taxa_cents
        reference = f"dlv_{delivery_id}"
        customer = Customer(name=customer_name, document=customer_document, email=customer_email)
        # May raise PaymentGatewayError (refusal / outage) — propagated to the caller.
        result = await self._payment.charge_with_split(
            amount_cents=amount,
            splits=splits,
            reference=reference,
            method=method,
            customer=customer,
        )
        await self._record(
            area_id=area_id,
            idempotency_key=reference,
            transaction_id=result.transaction_id,
            amount_cents=amount,
            method=method,
            kind="delivery",
            status="paid" if result.status == "paid" else "open",
            delivery_id=delivery_id,
        )
        if hold_escrow and courier_id is not None:
            await escrow.hold(
                self._session,
                area_id=area_id,
                delivery_id=delivery_id,
                courier_id=courier_id,
                amount_cents=corrida_cents,
            )
        logger.info(
            "payment.charge_delivery", area_id=area_id, delivery_id=delivery_id, method=method
        )
        return result

    # -----------------------------------------------------------------------
    # Refund (RN-004) — area-scoped (IDOR → 404, TH-H); distinct Pix/Card route.
    # -----------------------------------------------------------------------
    async def refund_charge(
        self,
        *,
        area_id: int,
        idempotency_key: str,
        state: str,
        return_pct: int,
    ) -> int:
        """Refund a charge the area owns; amount per RN-004. Returns the cents refunded.

        The charge is loaded scoped to `area_id` (in the WHERE clause) → 404 for another
        area's charge (TH-H, never 403). The refund route differs Pix vs Card (A9). A
        zero refund (e.g. post-collection with no excess) is a no-op.
        """
        charge = await repo.get_charge_for_area(
            self._session, idempotency_key=idempotency_key, area_id=area_id
        )
        if charge is None:
            raise NotFoundError("Cobrança não encontrada.")
        amount = refund_amount_cents(
            state=state, charged_cents=charge.amount_cents, return_pct=return_pct
        )
        if amount <= 0:
            return 0
        if charge.transaction_id is not None:
            await self._payment.refund(
                transaction_id=charge.transaction_id,
                amount_cents=amount,
                method=charge.method,
            )
        charge.status = "refunded"
        await self._session.flush()
        logger.info("payment.refund", area_id=area_id, delivery_id=charge.delivery_id)
        return amount
