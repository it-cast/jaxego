"""Withdrawal service (Phase 15 — REQ-038 / D-04 / TH-01/TH-02).

A courier withdraws from the RELEASED escrow balance via the `PaymentPort.payout`
(repasse). Rules (all parametrised — D-07):
- minimum: `withdrawal_min_cents` ([ASSUMIDO R$ 20]) → below is rejected;
- amount ≤ available balance (released escrow − non-failed withdrawals), computed under
  `SELECT ... FOR UPDATE` on the escrow rows so two concurrent withdrawals serialise
  (anti double-spend — TH-02);
- idempotency: one payout per `reference` (UNIQUE) → a retried request is a no-op (TH-02);
- failure compensation: a payout that fails marks the withdrawal `failed` (which frees
  the balance — failed withdrawals don't count), idempotent;
- scope: the withdrawal is bound to the requesting courier's (area_id, courier_id) —
  IDOR closed in the WHERE clause (TH-01).

Money in integer cents (DRV-009); datetimes aware UTC (TD-010). Never moves money
without the payout call returning success (TH-07).
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.couriers.models import Courier
from app.payments.errors import PaymentGatewayError
from app.withdrawals import repo
from app.withdrawals.models import Withdrawal

logger = structlog.get_logger("withdrawals")


class WithdrawalBelowMinimumError(AppError):
    """The requested amount is below the minimum withdrawal (D-04)."""

    status_code = 422
    code = "withdrawal_below_minimum"

    def __init__(self, minimum_cents: int) -> None:
        self.minimum_cents = minimum_cents
        super().__init__(f"O valor mínimo para saque é de R$ {minimum_cents / 100:.2f}.")


class CourierSubaccountMissingError(AppError):
    """Courier has no Safe2Pay subaccount yet — nowhere to send the payout."""

    status_code = 422
    code = "courier_subaccount_missing"

    def __init__(self) -> None:
        super().__init__("Sua conta na Safe2Pay ainda não foi configurada. Aguarde a aprovação do cadastro.")


class InsufficientBalanceError(AppError):
    """The requested amount exceeds the withdrawable balance."""

    status_code = 422
    code = "insufficient_balance"

    def __init__(self) -> None:
        super().__init__("Saldo insuficiente para o saque solicitado.")


async def available_balance(session: AsyncSession, *, area_id: int, courier_id: int) -> int:
    """The courier's withdrawable balance in cents (locks the released holds — TH-02)."""
    return await repo.available_balance_cents(session, area_id=area_id, courier_id=courier_id)


async def request_withdrawal(
    session: AsyncSession,
    *,
    area_id: int,
    courier_id: int,
    amount_cents: int,
    reference: str,
    payment,  # PaymentPort
    now: datetime | None = None,
) -> Withdrawal:
    """Request a withdrawal: validate, lock balance, payout, settle (D-04 / TH-01/TH-02).

    Idempotent by `reference`: a retried request returns the existing withdrawal without a
    second payout. On payout failure the withdrawal ends `failed` (the balance is restored
    — failed rows don't count). The caller commits.
    """
    now = now or datetime.now(UTC)

    # Idempotency: a re-request with the same reference returns the existing row (TH-02).
    existing = await repo.get_by_reference(session, reference=reference)
    if existing is not None:
        return existing

    # Minimum (D-04) — below is rejected before any balance read.
    if amount_cents < settings.withdrawal_min_cents:
        raise WithdrawalBelowMinimumError(settings.withdrawal_min_cents)

    # Balance under FOR UPDATE on the released holds (TH-02 — serialise concurrent saques).
    balance = await repo.available_balance_cents(session, area_id=area_id, courier_id=courier_id)
    if amount_cents > balance:
        raise InsufficientBalanceError()

    # Subconta Safe2Pay é o destino real da transferência (InternalTransfer usa o
    # Id numérico da subconta, não um identificador sintético) — sem ela, nada a fazer.
    courier = await session.get(Courier, courier_id)
    if courier is None or not courier.s2p_recipient_id:
        raise CourierSubaccountMissingError()

    # Reserve the balance: insert the withdrawal PENDING (counts against the balance now,
    # so a concurrent withdrawal blocked on the FOR UPDATE sees it once committed — TH-02).
    withdrawal = Withdrawal(
        area_id=area_id,
        courier_id=courier_id,
        reference=reference,
        amount_cents=amount_cents,
        status="pending",
    )
    session.add(withdrawal)
    await session.flush()

    # Repasse via the PaymentPort (never move money without the call — TH-07).
    try:
        result = await payment.payout(
            recipient=courier.s2p_recipient_id, amount_cents=amount_cents, reference=reference
        )
    except PaymentGatewayError as exc:
        # Compensation: the payout failed → mark failed (frees the balance), idempotent.
        withdrawal.status = "failed"
        withdrawal.failure_reason = str(exc)[:255]
        await session.flush()
        logger.warning("withdrawal.failed", area_id=area_id, courier_id=courier_id)
        return withdrawal

    withdrawal.status = "paid"
    withdrawal.transaction_id = result.transaction_id
    withdrawal.settled_at = now
    await session.flush()
    logger.info(
        "withdrawal.paid", area_id=area_id, courier_id=courier_id, amount_cents=amount_cents
    )
    return withdrawal
