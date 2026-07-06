"""PaymentStubAdapter — deterministic, offline. Tests NEVER touch Safe2Pay (D-09).

`scenario` drives the behaviour:
  - "approved" (default): every charge returns a fixed paid `ChargeResult`.
  - "refused": every charge raises `PaymentGatewayError` (F-03 E3 / card refused).
  - "down": every call raises `PaymentGatewayError` (circuit breaker — REQ-034).

Determinism: the transaction id is `stub_tx_{n}` (a per-instance counter), the token is
`stub_token`, and PIX returns a fixed QR. `refund_routes` records the URL-route used per
transaction so a test can assert Pix ≠ Card (A9). `statement_entries` is settable so the
reconciliation test can inject a matching / diverging extrato.
"""

from __future__ import annotations

from datetime import datetime
from itertools import count

from app.payments.errors import PaymentGatewayError
from app.payments.port import (
    CardData,
    ChargeResult,
    Customer,
    PayoutResult,
    Split,
    StatementEntry,
)


class PaymentStubAdapter:
    """In-memory deterministic Safe2Pay stand-in (no network)."""

    def __init__(self, *, scenario: str = "approved", payout_fails: bool = False) -> None:
        self.scenario = scenario
        # When True, `payout` raises PaymentGatewayError (saque falha → restitui — D-04).
        self.payout_fails = payout_fails
        self._seq = count(1)
        self.refund_routes: dict[str, str] = {}
        self.statement_entries: list[tuple[str, int]] = []
        self.subaccount_seq = count(1)
        self.payouts: list[tuple[str, int, str]] = []  # (recipient, cents, reference)

    def _tx(self) -> str:
        return f"stub_tx_{next(self._seq)}"

    def _guard(self) -> None:
        if self.scenario == "down":
            raise PaymentGatewayError("Safe2Pay indisponível (stub down).")
        if self.scenario == "refused":
            raise PaymentGatewayError("Cartão recusado (stub refused).", code="refused")

    async def tokenize_card(self, card: CardData) -> str | None:
        self._guard()
        return "stub_token"

    async def charge_with_token(
        self,
        *,
        token: str,
        amount_cents: int,
        reference: str,
        customer: Customer,
        card_data: CardData | None = None,
    ) -> ChargeResult:
        self._guard()
        return ChargeResult(transaction_id=self._tx(), status="paid", token=token)

    async def charge_with_split(
        self,
        *,
        amount_cents: int,
        splits: list[Split],
        reference: str,
        method: str,
        customer: Customer,
    ) -> ChargeResult:
        self._guard()
        # Defensive: the stub asserts the invariant so a broken split fails in tests too.
        if amount_cents != sum(s.amount_cents for s in splits):
            raise PaymentGatewayError("split soma diferente de amount (stub).")
        return ChargeResult(transaction_id=self._tx(), status="paid")

    async def create_pix_authorization(
        self,
        *,
        amount_cents: int,
        customer: Customer,
        reference: str,
        recorrente: bool = False,
    ) -> ChargeResult:
        self._guard()
        tx = self._tx()
        if recorrente:
            # Stub: simulates PIX Automático authorization (payer approves in banking app).
            return ChargeResult(
                transaction_id=tx,
                status="pending",
                qr_code=f"stub_pix_auto_link_{tx}",
                qr_code_base64=None,
                authorization_id=f"stub_auth_{tx}",
            )
        return ChargeResult(
            transaction_id=tx,
            status="pending",
            qr_code="00020101stub-pix-copy-paste",
            qr_code_base64="c3R1Yi1xci1iYXNlNjQ=",
            authorization_id="",
        )

    async def create_pix_charge_schedule(
        self,
        *,
        authorization_id: str,
        amount_cents: int,
        reference: str,
        due_date: str,
        description: str,
    ) -> "PixScheduleResult":
        self._guard()
        from app.payments.port import PixScheduleResult

        return PixScheduleResult(schedule_id=f"stub_sched_{next(self._seq)}", status="CRIADA")

    async def refund(self, *, transaction_id: str, amount_cents: int, method: str) -> None:
        self._guard()
        # Distinct route per method (A9): Pix vs Card use different endpoints.
        route = "v2/Transaction/Refund" if method == "pix" else "v2/CreditCard/Reverse"
        self.refund_routes[transaction_id] = route

    async def register_subaccount(
        self, *, courier_id: int, mei_cnpj: str, pix_key: str | None
    ) -> str:
        self._guard()
        return f"stub_recipient_{next(self.subaccount_seq)}"

    async def get_statement(self, *, since: datetime, until: datetime) -> list[StatementEntry]:
        self._guard()
        return [
            StatementEntry(transaction_id=tx, amount_cents=amt)
            for tx, amt in self.statement_entries
        ]

    async def payout(self, *, recipient: str, amount_cents: int, reference: str) -> PayoutResult:
        self._guard()
        if self.payout_fails:
            # The repasse failed at the PSP — the caller must restore the balance (D-04).
            raise PaymentGatewayError("repasse recusado (stub payout_fails).", code="payout_failed")
        self.payouts.append((recipient, amount_cents, reference))
        return PayoutResult(transaction_id=self._tx(), status="paid")
