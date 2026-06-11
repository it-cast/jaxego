"""PaymentPort Protocol + frozen result/data dataclasses (ADR-009 v2 / D-09).

Mirrors `app/integrations/base.py`: a `typing.Protocol` the service depends on, never a
concrete impl. Money is integer CENTS in every dataclass (`amount_cents` — DRV-009).
`Split` carries the recipient + its cents; the invariant `amount == Σ splits` is
checked at the call site (TH-F). `CardData`/`Customer` are opaque value objects — the
card fields exist transiently in memory only and are NEVER logged/persisted (A09).

The methods cover the whole Safe2Pay surface this phase needs:
  - tokenize_card / charge_with_token  — recurring card (SAAS-BILLING §5)
  - charge_with_split                  — delivery split (F-03 / TH-F)
  - create_pix_authorization           — PIX automático (SAAS-BILLING §5.5)
  - refund                             — distinct Pix vs Card route (A9)
  - register_subaccount                — courier subaccount on MEI approval (RN-010)
  - get_statement                      — daily reconciliation (D-08)
  - payout                             — courier withdrawal repasse (Phase 15 — REQ-038)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Customer:
    """The payer block sent to Safe2Pay. `document` is CPF/CNPJ (masked in any log)."""

    name: str
    document: str
    email: str


@dataclass(frozen=True)
class CardData:
    """Decrypted card — transient, in-memory ONLY. NEVER logged/persisted (A09)."""

    holder: str
    number: str
    expiration: str  # MM/YYYY
    cvv: str


@dataclass(frozen=True)
class Split:
    """One split leg: a recipient and its share in integer cents (TH-F)."""

    recipient: str
    amount_cents: int


@dataclass(frozen=True)
class ChargeResult:
    """Outcome of a charge. `transaction_id` is the Safe2Pay IdTransaction (idempotency)."""

    transaction_id: str
    status: str  # authorized | paid | refused | pending
    qr_code: str | None = None  # PIX copia-e-cola (EMV)
    qr_code_base64: str | None = None  # PIX QR image
    authorization_id: str | None = None  # PIX automático autorização id
    token: str | None = None  # tokenization (None in sandbox — Pitfall 5)


@dataclass(frozen=True)
class StatementEntry:
    """One Safe2Pay statement line for reconciliation (cents, exact — TH-I)."""

    transaction_id: str
    amount_cents: int


@dataclass(frozen=True)
class PayoutResult:
    """Outcome of a courier withdrawal repasse (Phase 15 — REQ-038)."""

    transaction_id: str
    status: str  # paid | pending


class PaymentPort(Protocol):
    """Safe2Pay surface behind a stable interface (D-09). Never raises card PII."""

    async def tokenize_card(self, card: CardData) -> str | None: ...

    async def charge_with_token(
        self, *, token: str, amount_cents: int, reference: str, customer: Customer
    ) -> ChargeResult: ...

    async def charge_with_split(
        self,
        *,
        amount_cents: int,
        splits: list[Split],
        reference: str,
        method: str,
        customer: Customer,
    ) -> ChargeResult: ...

    async def create_pix_authorization(
        self, *, amount_cents: int, customer: Customer, reference: str
    ) -> ChargeResult: ...

    async def refund(self, *, transaction_id: str, amount_cents: int, method: str) -> None: ...

    async def register_subaccount(
        self, *, courier_id: int, mei_cnpj: str, pix_key: str | None
    ) -> str: ...

    async def get_statement(self, *, since: datetime, until: datetime) -> list[StatementEntry]: ...

    async def payout(
        self, *, recipient: str, amount_cents: int, reference: str
    ) -> PayoutResult: ...
