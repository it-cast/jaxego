"""Courier withdrawal (Phase 15 — REQ-038 / D-04 / TH-01/TH-02).

Saldo de escrow liberado → saque via PaymentPort.payout. Cobre: saque < R$20 rejeitado;
saque > saldo rejeitado; saque feliz debita o saldo; saque falha → saldo restituído
(compensação); idempotência por reference; IDOR (saldo escopado ao próprio courier).
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_balance_is_released_minus_withdrawn(withdrawal_seed, session_factory) -> None:
    from app.withdrawals import service

    async with session_factory() as s:
        balance = await service.available_balance(
            s, area_id=withdrawal_seed.area_a_id, courier_id=withdrawal_seed.courier_id
        )
        assert balance == 2500  # 1000 + 1500 released; the HELD 9999 does not count


@pytest.mark.asyncio
async def test_below_minimum_rejected(withdrawal_seed, session_factory, payment_stub) -> None:
    from app.withdrawals.service import WithdrawalBelowMinimumError, request_withdrawal

    async with session_factory() as s:
        with pytest.raises(WithdrawalBelowMinimumError):
            await request_withdrawal(
                s,
                area_id=withdrawal_seed.area_a_id,
                courier_id=withdrawal_seed.courier_id,
                amount_cents=1900,  # < R$ 20,00
                reference="wd_below_1",
                payment=payment_stub,
            )
        await s.commit()


@pytest.mark.asyncio
async def test_above_balance_rejected(withdrawal_seed, session_factory, payment_stub) -> None:
    from app.withdrawals.service import InsufficientBalanceError, request_withdrawal

    async with session_factory() as s:
        with pytest.raises(InsufficientBalanceError):
            await request_withdrawal(
                s,
                area_id=withdrawal_seed.area_a_id,
                courier_id=withdrawal_seed.courier_id,
                amount_cents=2600,  # > 2500 balance
                reference="wd_over_1",
                payment=payment_stub,
            )
        await s.commit()


@pytest.mark.asyncio
async def test_successful_withdrawal_debits_balance(
    withdrawal_seed, session_factory, payment_stub
) -> None:
    from app.withdrawals import service

    async with session_factory() as s:
        w = await service.request_withdrawal(
            s,
            area_id=withdrawal_seed.area_a_id,
            courier_id=withdrawal_seed.courier_id,
            amount_cents=2000,
            reference="wd_ok_1",
            payment=payment_stub,
        )
        await s.commit()
        assert w.status == "paid"
        assert w.transaction_id is not None

    # Balance reduced by the paid withdrawal: 2500 - 2000 = 500.
    async with session_factory() as s:
        balance = await service.available_balance(
            s, area_id=withdrawal_seed.area_a_id, courier_id=withdrawal_seed.courier_id
        )
        assert balance == 500
    # The Stub recorded exactly one payout.
    assert len(payment_stub.payouts) == 1


@pytest.mark.asyncio
async def test_failed_payout_restores_balance(
    withdrawal_seed, session_factory, payout_failing_stub
) -> None:
    from app.withdrawals import service

    async with session_factory() as s:
        w = await service.request_withdrawal(
            s,
            area_id=withdrawal_seed.area_a_id,
            courier_id=withdrawal_seed.courier_id,
            amount_cents=2000,
            reference="wd_fail_1",
            payment=payout_failing_stub,
        )
        await s.commit()
        assert w.status == "failed"
        assert w.failure_reason is not None

    # Balance is restored — a failed withdrawal does NOT count against the balance.
    async with session_factory() as s:
        balance = await service.available_balance(
            s, area_id=withdrawal_seed.area_a_id, courier_id=withdrawal_seed.courier_id
        )
        assert balance == 2500


@pytest.mark.asyncio
async def test_idempotent_by_reference(withdrawal_seed, session_factory, payment_stub) -> None:
    from app.withdrawals import service

    async with session_factory() as s:
        first = await service.request_withdrawal(
            s,
            area_id=withdrawal_seed.area_a_id,
            courier_id=withdrawal_seed.courier_id,
            amount_cents=2000,
            reference="wd_idem_1",
            payment=payment_stub,
        )
        await s.commit()
        first_id = first.id

    async with session_factory() as s:
        again = await service.request_withdrawal(
            s,
            area_id=withdrawal_seed.area_a_id,
            courier_id=withdrawal_seed.courier_id,
            amount_cents=2000,
            reference="wd_idem_1",  # same reference
            payment=payment_stub,
        )
        await s.commit()
        assert again.id == first_id  # no second withdrawal

    # Only one payout happened despite two requests.
    assert len(payment_stub.payouts) == 1


@pytest.mark.asyncio
async def test_balance_scoped_to_courier_idor(withdrawal_seed, session_factory) -> None:
    """The other courier in area B has no released balance (IDOR — TH-01)."""
    from app.withdrawals import service

    async with session_factory() as s:
        balance = await service.available_balance(
            s, area_id=withdrawal_seed.area_b_id, courier_id=withdrawal_seed.other_courier_id
        )
        assert balance == 0
