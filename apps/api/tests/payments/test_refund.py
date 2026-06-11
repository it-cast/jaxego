"""Refunds: RN-004 amount, IDOR (404 for other area), distinct Pix vs Card route.

TH-H: a refund is scoped by area in the WHERE clause → 404 for another area's charge,
never 403. RN-004: pre-acceptance total; post-collection 100%+return.
"""

from __future__ import annotations

import pytest


def test_refund_amount_pre_acceptance_total() -> None:
    from app.payments.fees import refund_amount_cents

    # CRIADA (pre-acceptance) → full refund of what was charged.
    assert refund_amount_cents(state="CRIADA", charged_cents=1200, return_pct=20) == 1200


def test_refund_amount_post_collection() -> None:
    from app.payments.fees import refund_amount_cents

    # COLETADA → keep 100% + return policy; refund is the excess only.
    # charged 1200, cost = 1200 + 20% return = 1440 capped at charged → refund 0.
    assert refund_amount_cents(state="COLETADA", charged_cents=1200, return_pct=20) == 0


def test_refund_amount_accepted_half() -> None:
    from app.payments.fees import refund_amount_cents

    # ACEITA → 50% cost, refund the other half.
    assert refund_amount_cents(state="ACEITA", charged_cents=1200, return_pct=0) == 600


@pytest.mark.asyncio
async def test_refund_idor_other_area_404(payments_seed, payment_stub, session_factory) -> None:
    from app.core.exceptions import NotFoundError
    from app.payments import repo
    from app.payments.service import PaymentService

    async with session_factory() as s:
        await repo.record_charge(
            s,
            area_id=payments_seed.area_a_id,
            idempotency_key="dlv_77",
            transaction_id="tx_77",
            amount_cents=1200,
            method="card",
            kind="delivery",
            status="paid",
        )
        await s.commit()

    async with session_factory() as s:
        svc = PaymentService(s, payment=payment_stub)
        with pytest.raises(NotFoundError):
            # area_b cannot refund area_a's charge → 404.
            await svc.refund_charge(
                area_id=payments_seed.area_b_id,
                idempotency_key="dlv_77",
                state="CRIADA",
                return_pct=0,
            )


@pytest.mark.asyncio
async def test_refund_routes_distinct_pix_vs_card(payment_stub) -> None:
    """The Stub records the route used so we can assert Pix ≠ Card endpoint (A9)."""
    await payment_stub.refund(transaction_id="tx_a", amount_cents=500, method="pix")
    await payment_stub.refund(transaction_id="tx_b", amount_cents=500, method="card")
    assert payment_stub.refund_routes["tx_a"] != payment_stub.refund_routes["tx_b"]
