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

import unicodedata
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


def _ascii(s: str) -> str:
    """Remove accents — Safe2Pay rejects non-ASCII in address fields."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _s2p_phone(phone: str) -> str:
    """Strip country code +55 — Safe2Pay expects 10–11 digits with DDD only."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 13 and digits.startswith("55"):
        digits = digits[2:]
    return digits


def _normalize_expiry(expiry: str) -> str:
    """Normalize MM/YY → MM/YYYY. Safe2Pay requires 4-digit year."""
    parts = expiry.split("/")
    if len(parts) == 2 and len(parts[1]) == 2:
        return f"{parts[0]}/20{parts[1]}"
    return expiry


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
                # Read body BEFORE raise_for_status so it's available inside the context.
                if resp.status_code >= 400:
                    raw = resp.content.decode("utf-8", errors="replace")
                    try:
                        err_body = resp.json()
                        err_msg = (
                            err_body.get("Error")
                            or err_body.get("Message")
                            or raw[:500]
                        )
                        err_code = str(err_body.get("ErrorCode", ""))
                    except Exception:
                        err_msg, err_code = raw[:500], ""
                    logger.error(
                        "safe2pay_http_error",
                        status=resp.status_code,
                        s2p_error=err_msg,
                        s2p_code=err_code,
                    )
                    raise PaymentGatewayError(f"Safe2Pay HTTP {resp.status_code}")
                resp.raise_for_status()
        except PaymentGatewayError:
            raise
        except httpx.RequestError as exc:
            logger.error("safe2pay_network_error")  # no payload/PII
            raise PaymentGatewayError("Safe2Pay inacessível") from exc

        data = resp.json()
        if data.get("HasError"):  # ⚠ ignores HTTP status
            code = str(data.get("ErrorCode", "unknown"))
            msg = str(data.get("Error") or data.get("Message") or "")  # no PII in these fields
            logger.error("safe2pay_business_error", error_code=code, s2p_message=msg)
            raise PaymentGatewayError(f"Safe2Pay erro {code}", code=code)
        return data.get("ResponseDetail", data)

    async def _post_v3(self, url: str, payload: dict) -> dict:
        """POST to a Safe2Pay v3 endpoint (REST conventions — no HasError wrapper)."""
        assert_safe_url(url, allowlist=self._allowlist)
        try:
            async with build_client(timeout=httpx.Timeout(30.0)) as client:
                resp = await client.post(url, json=payload, headers=self._headers())
                if resp.status_code >= 400:
                    raw = resp.content.decode("utf-8", errors="replace")
                    try:
                        err_body = resp.json()
                        err_msg = (
                            err_body.get("Error")
                            or err_body.get("Message")
                            or err_body.get("detail")
                            or raw[:500]
                        )
                        err_code = str(err_body.get("ErrorCode") or err_body.get("code", ""))
                    except Exception:
                        err_msg, err_code = raw[:500], ""
                    logger.error(
                        "safe2pay_v3_http_error",
                        status=resp.status_code,
                        s2p_error=err_msg,
                        s2p_code=err_code,
                        url=url,
                    )
                    raise PaymentGatewayError(f"Safe2Pay HTTP {resp.status_code}")
                resp.raise_for_status()
        except PaymentGatewayError:
            raise
        except httpx.RequestError as exc:
            logger.error("safe2pay_v3_network_error")
            raise PaymentGatewayError("Safe2Pay inacessível") from exc
        return resp.json()

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
        self,
        *,
        token: str,
        amount_cents: int,
        reference: str,
        customer: Customer,
        card_data: CardData | None = None,
    ) -> ChargeResult:
        # Sandbox: token-based flow doesn't work (Pitfall 5). Use direct card data instead.
        if self._sandbox and card_data is not None:
            payment_object = {
                "CardNumber": card_data.number,
                "Holder": card_data.holder,
                "ExpirationDate": _normalize_expiry(card_data.expiration),
                "SecurityCode": card_data.cvv,
                "InstallmentQuantity": 1,
            }
            is_sandbox = True
            result_token = None  # sandbox never returns a storable token (A09)
        else:
            payment_object = {"Token": token, "InstallmentQuantity": 1}
            is_sandbox = False  # recurring token only works in production (Pitfall 5)
            result_token = token

        amount = amount_cents / 100
        logger.info(
            "safe2pay_charge_attempt",
            is_sandbox=is_sandbox,
            amount=amount,
            payment_method=2,
            token_present=bool(payment_object.get("Token")),
            token_prefix=str(payment_object.get("Token", ""))[:8] if payment_object.get("Token") else None,
        )
        data = await self._call_safe2pay(
            f"{self._payment_url}/v2/payment",
            {
                "IsSandbox": is_sandbox,
                "Reference": reference,
                "Amount": amount,
                "PaymentMethod": 2,
                "PaymentObject": payment_object,
                "Customer": {
                    "Name": customer.name,
                    "Identity": customer.document,
                    "Email": customer.email,
                },
                "Products": [
                    {
                        "Code": "ASSINATURA",
                        "Description": "Assinatura",
                        "UnitPrice": amount,
                        "Quantity": 1,
                    }
                ],
            },
        )
        status = str(data.get("Status", ""))
        return ChargeResult(
            transaction_id=str(data.get("IdTransaction", "")),
            status="paid" if status in _APPROVED else "refused",
            token=result_token,
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
        self,
        *,
        amount_cents: int,
        customer: Customer,
        reference: str,
        recorrente: bool = False,
    ) -> ChargeResult:
        if recorrente:
            return await self._create_pix_automatic(
                amount_cents=amount_cents, customer=customer, reference=reference
            )
        return await self._create_pix_qr(
            amount_cents=amount_cents, customer=customer, reference=reference
        )

    async def _create_pix_qr(
        self, *, amount_cents: int, customer: Customer, reference: str
    ) -> ChargeResult:
        # PIX simples (avulso) via /v2/payment (PaymentMethod 10) — gera QR Code único.
        amount = amount_cents / 100
        logger.info(
            "safe2pay_pix_qr_attempt",
            is_sandbox=self._sandbox,
            amount=amount,
            payment_method=10,
        )
        data = await self._call_safe2pay(
            f"{self._payment_url}/v2/payment",
            {
                "IsSandbox": self._sandbox,
                "Reference": reference,
                "Amount": amount,
                "PaymentMethod": "10",
                "Customer": {
                    "Name": customer.name,
                    "Identity": customer.document,
                    "Email": customer.email,
                },
                "PaymentObject": {},
            },
        )
        pix_obj = data.get("PaymentObject") or {}
        return ChargeResult(
            transaction_id=str(data.get("IdTransaction", "")),
            status="pending",
            qr_code=pix_obj.get("Key"),
            qr_code_base64=pix_obj.get("QrCode"),
            authorization_id="",
        )

    async def _create_pix_automatic(
        self, *, amount_cents: int, customer: Customer, reference: str
    ) -> ChargeResult:
        # PIX Automático BACEN — POST /v3/pix/automatic/authorizations.
        # Sandbox NOT available (Safe2Pay docs). Always uses production endpoint.
        # Payload validated against official OpenAPI spec (July 2026).
        amount = amount_cents / 100
        today = datetime.now().date().isoformat()
        logger.info(
            "safe2pay_pix_automatic_attempt",
            is_sandbox=self._sandbox,
            amount=amount,
        )
        payload: dict = {
            "Application": "Jaxegô",
            "Contract": {
                "Description": "Assinatura mensal Jaxegô",
                "Name": "Assinatura Jaxegô",
                "Customer": {
                    "Identity": customer.document,
                    "Name": customer.name,
                    "Email": customer.email,
                    "Phone": _s2p_phone(customer.phone or ""),
                    "Address": {
                        "ZipCode": (customer.zip_code or "").replace("-", ""),
                        "Street": _ascii(customer.street or ""),
                        "Number": customer.street_number or "S/N",
                        "Complement": "",
                        "District": _ascii(customer.neighborhood or ""),
                        "StateInitials": customer.state or "",
                        "CityName": _ascii(customer.city or ""),
                        "CountryName": "Brasil",
                    },
                },
            },
            "Calendar": {
                "StartDate": today,
                "Periodicity": "MENSAL",
                "RetryPolicy": "PERMITE_3R_7D",
            },
            "Amount": {"Fixed": amount},
            "ImmediatePayment": {
                "Amount": amount,
                "Reference": reference,
            },
        }
        raw = await self._post_v3(
            f"{self._payment_url}/v3/pix/automatic/authorizations",
            payload,
        )
        # v3 response: {"traceId": "...", "data": {"Id": ..., "QrData": {...}, ...}}
        data = raw.get("data", raw)
        auth_id = str(data.get("Id", ""))
        qr_data = data.get("QrData") or {}
        immediate = data.get("ImmediatePayment") or {}
        return ChargeResult(
            transaction_id=str(immediate.get("IdTransaction") or auth_id),
            status="pending",
            qr_code=qr_data.get("PixCopyAndPaste"),
            qr_code_base64=qr_data.get("QrCode"),  # URL da imagem, não base64
            authorization_id=auth_id,
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
        # [ASSUMIDO DEC-PIX-02] POST /v3/.../chargeSchedules per Safe2Pay docs (July 2026).
        # Calendar.DueDate format: YYYY-MM-DD.
        from app.payments.port import PixScheduleResult

        data = await self._post_v3(
            f"{self._payment_url}/v3/pix/automatic/authorizations/{authorization_id}/chargeSchedules",
            {
                "Application": "Jaxegô",
                "Reference": reference,
                "Calendar": {"DueDate": due_date},
                "Amount": amount_cents / 100,
                "AdditionalInformation": description,
            },
        )
        return PixScheduleResult(
            schedule_id=str(data.get("Id", "")),
            status=str(data.get("Status", "CRIADA")),
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
