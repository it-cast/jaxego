"""Safe2PayHttpAdapter — the real httpx impl (staging/production only).

The whole point of `_call_safe2pay` (skill A2): HTTP 200 from Safe2Pay does NOT mean
success — the body carries `HasError`. This central helper ALWAYS checks it, ALWAYS
guards the URL through `assert_safe_url` (SSRF / TH-L), and NEVER logs the payload (card
PII / A09). The three subdomains are separate base URLs (skill A1): `payment` creates,
`api` administers (refund/subaccount), `services` queries (statement) — never concatenate
a subdomain.

⚠ DEC-003 `[ASSUMIDO]`: the exact Safe2Pay payload shapes for split, PIX automático,
refund routes, subaccount and statement are NOT confirmed (A1/A2/A3/A4/A9). They are
isolated HERE behind `PaymentPort` and validated at T-13 against the real contract; an
ADR then supersedes DEC-003 and only this file changes. The tests NEVER exercise this
adapter — they use `PaymentStubAdapter` (D-09).
"""

from __future__ import annotations

from datetime import datetime

import httpx
import structlog

from app.integrations.http import assert_safe_url, build_client
from app.payments.errors import PaymentGatewayError
from app.payments.port import (
    CardData,
    ChargeResult,
    Customer,
    PayoutResult,
    Split,
    StatementEntry,
)

logger = structlog.get_logger("payments.safe2pay")

# Safe2Pay approved statuses (SAAS-BILLING §5.2).
_APPROVED = {"3", "4"}


class Safe2PayHttpAdapter:
    """Real Safe2Pay client. Every call passes `_call_safe2pay` (HasError + SSRF)."""

    def __init__(
        self,
        *,
        api_key: str | None,
        payment_url: str,
        api_url: str,
        services_url: str,
        allowlist: set[str],
        sandbox: bool = True,
        jaxego_recipient: str | None = None,
    ) -> None:
        self._api_key = api_key or ""
        self._payment_url = payment_url.rstrip("/")
        self._api_url = api_url.rstrip("/")
        self._services_url = services_url.rstrip("/")
        self._allowlist = allowlist
        self._sandbox = sandbox
        self._jaxego_recipient = jaxego_recipient

    def _headers(self) -> dict[str, str]:
        # x-api-key only; NEVER logged (A09).
        return {"x-api-key": self._api_key, "Content-Type": "application/json"}

    async def _call_safe2pay(self, url: str, payload: dict) -> dict:
        """POST to Safe2Pay; raise on HasError even when HTTP is 200 (skill A2)."""
        assert_safe_url(url, allowlist=self._allowlist)  # A10 SSRF (before connect)
        try:
            async with build_client(timeout=httpx.Timeout(30.0)) as client:
                resp = await client.post(url, json=payload, headers=self._headers())
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("safe2pay_http_error", status=exc.response.status_code)  # no payload
            raise PaymentGatewayError(f"Safe2Pay HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("safe2pay_network_error")  # no payload/PII
            raise PaymentGatewayError("Safe2Pay inacessível") from exc

        data = resp.json()
        if data.get("HasError"):  # ⚠ ignores HTTP status
            code = str(data.get("ErrorCode", "unknown"))
            logger.error("safe2pay_business_error", error_code=code)  # no card payload
            raise PaymentGatewayError(f"Safe2Pay erro {code}", code=code)
        return data.get("ResponseDetail", data)

    # --- PaymentPort impl ([ASSUMIDO] shapes — DEC-003) ---
    async def tokenize_card(self, card: CardData) -> str | None:
        # Sandbox does not return a token (Pitfall 5) — caller charges raw there.
        if self._sandbox:
            return None
        data = await self._call_safe2pay(
            f"{self._payment_url}/v2/token",
            {
                "Holder": card.holder,
                "CardNumber": card.number,
                "ExpirationDate": card.expiration,
                "SecurityCode": card.cvv,
            },
        )
        return data.get("Token")

    async def charge_with_token(
        self, *, token: str, amount_cents: int, reference: str, customer: Customer
    ) -> ChargeResult:
        data = await self._call_safe2pay(
            f"{self._payment_url}/v2/payment",
            {
                "IsSandbox": False,  # recurring token only works in production (Pitfall 5)
                "Reference": reference,
                "PaymentMethod": "2",
                "PaymentObject": {"Token": token, "InstallmentQuantity": 1},
                "Customer": {
                    "Name": customer.name,
                    "Identity": customer.document,
                    "Email": customer.email,
                },
                "Products": [
                    {
                        "Code": "ASSINATURA",
                        "Description": "Assinatura",
                        "UnitPrice": amount_cents / 100,
                        "Quantity": 1,
                    }
                ],
            },
        )
        status = str(data.get("Status", ""))
        return ChargeResult(
            transaction_id=str(data.get("IdTransaction", "")),
            status="paid" if status in _APPROVED else "refused",
            token=token,
        )

    async def charge_with_split(
        self,
        *,
        amount_cents: int,
        splits: list[Split],
        reference: str,
        method: str,
        customer: Customer,
    ) -> ChargeResult:
        # [ASSUMIDO A2] Splits:[{Recipient,Amount}] — confirm at T-13.
        data = await self._call_safe2pay(
            f"{self._payment_url}/v2/payment",
            {
                "IsSandbox": self._sandbox,
                "Reference": reference,
                "Amount": amount_cents / 100,
                "PaymentMethod": "2" if method == "card" else "10",
                "Splits": [
                    {"Recipient": s.recipient, "Amount": s.amount_cents / 100} for s in splits
                ],
                "Customer": {
                    "Name": customer.name,
                    "Identity": customer.document,
                    "Email": customer.email,
                },
            },
        )
        status = str(data.get("Status", ""))
        return ChargeResult(
            transaction_id=str(data.get("IdTransaction", "")),
            status="paid" if status in _APPROVED else "pending",
            qr_code=(data.get("PaymentObject") or {}).get("Key"),
            qr_code_base64=(data.get("PaymentObject") or {}).get("QrCode"),
        )

    async def create_pix_authorization(
        self, *, amount_cents: int, customer: Customer, reference: str
    ) -> ChargeResult:
        # [ASSUMIDO] v3 PIX automático (SAAS-BILLING §5.5) — confirm at T-13.
        data = await self._call_safe2pay(
            f"{self._payment_url}/v3/pix/automatic/authorizations",
            {
                "Contract": {
                    "Description": reference,
                    "Customer": {"Identity": customer.document, "Name": customer.name},
                },
                "Calendar": {"Periodicity": "MENSAL", "RetryPolicy": "PERMITE_3R_7D"},
                "Amount": {"Fixed": amount_cents / 100},
                "ImmediatePayment": {"Amount": amount_cents / 100, "Reference": reference},
            },
        )
        obj = data.get("data", data)
        qr = obj.get("qrData", {})
        return ChargeResult(
            transaction_id=str((obj.get("immediatePayment") or {}).get("idTransaction", "")),
            status="pending",
            qr_code=qr.get("pixCopyAndPaste"),
            qr_code_base64=qr.get("qrCode"),
            authorization_id=str(obj.get("id", "")),
        )

    async def refund(self, *, transaction_id: str, amount_cents: int, method: str) -> None:
        # [ASSUMIDO A9] distinct route Pix vs Card — confirm at T-13.
        route = (
            f"{self._api_url}/v2/Transaction/Refund"
            if method == "pix"
            else f"{self._api_url}/v2/CreditCard/Reverse"
        )
        await self._call_safe2pay(
            route, {"IdTransaction": transaction_id, "Amount": amount_cents / 100}
        )

    async def register_subaccount(
        self, *, courier_id: int, mei_cnpj: str, pix_key: str | None
    ) -> str:
        # [ASSUMIDO A3] subaccount API — may require manual registration; confirm at T-13.
        data = await self._call_safe2pay(
            f"{self._api_url}/v2/marketplace/subaccount",
            {"Identity": mei_cnpj, "PixKey": pix_key},
        )
        return str(data.get("RecipientId", ""))

    async def get_statement(self, *, since: datetime, until: datetime) -> list[StatementEntry]:
        data = await self._call_safe2pay(
            f"{self._services_url}/v2/statement",
            {"Since": since.isoformat(), "Until": until.isoformat()},
        )
        rows = data.get("Entries", []) if isinstance(data, dict) else []
        return [
            StatementEntry(
                transaction_id=str(r.get("IdTransaction", "")),
                amount_cents=int(round(float(r.get("Amount", 0)) * 100)),
            )
            for r in rows
        ]

    async def payout(self, *, recipient: str, amount_cents: int, reference: str) -> PayoutResult:
        # [ASSUMIDO — TD-15-01] Courier withdrawal repasse (transfer to subaccount). The
        # exact Safe2Pay endpoint/shape for a payout/transfer is NOT confirmed (the cutover
        # depends on the contract — DEC-003). Isolated HERE behind `PaymentPort`; the Stub
        # drives dev/test. Validated against the real contract at cutover; an ADR then
        # supersedes DEC-003 and only this file changes.
        data = await self._call_safe2pay(
            f"{self._api_url}/v2/marketplace/transfer",
            {
                "Recipient": recipient,
                "Amount": amount_cents / 100,
                "Reference": reference,
            },
        )
        return PayoutResult(
            transaction_id=str(data.get("IdTransaction", "")),
            status="paid" if str(data.get("Status", "")) in _APPROVED else "pending",
        )
