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
        marketplace_api_key: str | None = None,
    ) -> None:
        self._api_key = api_key or ""
        self._payment_url = payment_url.rstrip("/")
        self._api_url = api_url.rstrip("/")
        self._services_url = services_url.rstrip("/")
        self._allowlist = allowlist
        self._sandbox = sandbox
        self._jaxego_recipient = jaxego_recipient
        # Token da conta matriz/Marketplace — só a matriz pode criar subcontas
        # via /v2/marketplace/add (uma subconta filha recebe erro 300 da S2P).
        self._marketplace_api_key = marketplace_api_key or api_key or ""

    def _headers(self) -> dict[str, str]:
        # x-api-key only; NEVER logged (A09).
        return {"x-api-key": self._api_key, "Content-Type": "application/json"}

    def _marketplace_headers(self) -> dict[str, str]:
        return {"x-api-key": self._marketplace_api_key, "Content-Type": "application/json"}

    async def _call_safe2pay(
        self, url: str, payload: dict, *, headers: dict[str, str] | None = None
    ) -> dict:
        """POST to Safe2Pay; raise on HasError even when HTTP is 200 (skill A2)."""
        assert_safe_url(url, allowlist=self._allowlist)  # A10 SSRF (before connect)
        try:
            async with build_client(timeout=httpx.Timeout(30.0)) as client:
                resp = await client.post(url, json=payload, headers=headers or self._headers())
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
        # PIX avulso via /v2/payment (PaymentMethod 6) — gera QR Code único.
        # PaymentMethod 6 = PIX (doc Safe2Pay: https://developers.safe2pay.com.br/reference/cobranca-criar)
        amount = amount_cents / 100
        logger.info(
            "safe2pay_pix_qr_attempt",
            is_sandbox=self._sandbox,
            amount=amount,
            payment_method=6,
        )
        from app.core.config import get_settings
        callback_url = get_settings().safe2pay_callback_url or ""
        data = await self._call_safe2pay(
            f"{self._payment_url}/v2/payment",
            {
                "IsSandbox": self._sandbox,
                "Application": "Jaxegô",
                "CallbackUrl": callback_url,
                "Reference": reference,
                "PaymentMethod": "6",
                "Customer": {
                    "Name": customer.name,
                    "Identity": customer.document,
                    "Email": customer.email,
                    "Address": {
                        "ZipCode": (customer.zip_code or "").replace("-", ""),
                        "Street": _ascii(customer.street or ""),
                        "Number": customer.street_number or "S/N",
                        "Complement": "",
                        "District": _ascii(customer.neighborhood or ""),
                        "CityName": "",
                        "StateInitials": customer.state or "",
                        "CountryName": "Brasil",
                    },
                },
                "Products": [
                    {
                        "Code": "ENTREGA",
                        "Description": "Entrega",
                        "UnitPrice": amount,
                        "Quantity": 1,
                    }
                ],
                "PaymentObject": {
                    "Expiration": 600,
                },
            },
        )
        # _call_safe2pay returns ResponseDetail directly.
        # Key = EMV copia-e-cola; QrCode = URL da imagem PNG do QR.
        return ChargeResult(
            transaction_id=str(data.get("IdTransaction", "")),
            status="pending",
            qr_code=data.get("Key"),
            qr_code_base64=data.get("QrCode"),
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
        auth_id = str(data.get("id") or data.get("Id") or "")
        qr_data = data.get("qrData") or data.get("QrData") or {}
        immediate = data.get("immediatePayment") or data.get("ImmediatePayment") or {}
        return ChargeResult(
            transaction_id=str(immediate.get("idTransaction") or immediate.get("IdTransaction") or auth_id),
            status="pending",
            qr_code=qr_data.get("pixCopyAndPaste") or qr_data.get("PixCopyAndPaste"),
            qr_code_base64=qr_data.get("qrCode") or qr_data.get("QrCode"),
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

    async def get_pix_authorization_status(self, *, authorization_id: str) -> str:
        """GET /v3/pix/automatic/authorizations/{id} — retorna status atual da autorização."""
        url = f"{self._payment_url}/v3/pix/automatic/authorizations/{authorization_id}"
        assert_safe_url(url, allowlist=self._allowlist)
        try:
            async with build_client(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.get(url, headers=self._headers())
                if resp.status_code >= 400:
                    return "ERRO"
                data = resp.json()
                detail = data.get("data", data)
                return str(detail.get("status") or "DESCONHECIDO").upper()
        except Exception:
            return "ERRO"

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
        result = await self.register_subaccount_full(courier=type("_C", (), {
            "full_name": "", "mei_cnpj": mei_cnpj, "email": "", "phone_e164": "",
            "birth_date": None, "zip_code": None, "street": None, "street_number": None,
            "complement": None, "neighborhood": None, "city": None, "state": None,
            "bank_code": None, "bank_agency": None, "bank_account": None,
            "bank_account_digit": None, "bank_account_type": None,
        })())
        return result.get("recipient_id", "")

    async def register_subaccount_full(self, *, courier: object) -> dict[str, str]:
        """Cria subconta no Safe2Pay Marketplace via /v2/marketplace/add.

        Identity: CNPJ do MEI quando existe; senão o CPF do entregador
        (pós-users o CPF vive na própria tabela couriers).
        """
        identity = getattr(courier, "mei_cnpj", None) or getattr(courier, "cpf", None) or ""
        # Responsável é sempre pessoa física — CPF (a conta MEI usa CNPJ só na Identity).
        responsible_identity = getattr(courier, "cpf", None) or identity
        phone = (getattr(courier, "phone_e164", "") or "").lstrip("+")
        birth = getattr(courier, "birth_date", None)

        payload: dict = {
            "Name": getattr(courier, "full_name", ""),
            "CommercialName": getattr(courier, "full_name", ""),
            "Identity": identity,
            "Email": getattr(courier, "email", ""),
            "ResponsibleName": getattr(courier, "full_name", ""),
            "ResponsibleIdentity": responsible_identity,
            "ResponsiblePhone": phone,
            "ResponsibleBirthDate": birth.strftime("%Y-%m-%d") if birth else "",
            "IsPanelRestricted": True,
            "IsTransferCheckingAccountDisabled": False,
            "Address": {
                "ZipCode": (getattr(courier, "zip_code", "") or "").replace("-", ""),
                "Street": getattr(courier, "street", "") or "",
                "Number": getattr(courier, "street_number", "") or "S/N",
                "Complement": getattr(courier, "complement", "") or "",
                "District": getattr(courier, "neighborhood", "") or "",
                "CityName": getattr(courier, "city", "") or "",
                "StateInitials": getattr(courier, "state", "") or "",
                "CountryName": "Brasil",
            },
            "MerchantSplit": [
                {
                    "PaymentMethodCode": "6",
                    "IsSubaccountTaxPayer": False,
                    # Taxa mínima exigida pela Safe2Pay para PIX (PaymentMethodCode
                    # 6) no cadastro da subconta — erro 1273 abaixo de 0,35. Não é
                    # o split real da corrida (isso é calculado à parte, por
                    # transação, em charge_with_split); é só a config da subconta.
                    "Taxes": [{"TaxTypeName": "2", "Tax": "0.35"}],
                }
            ],
        }

        bank_code = getattr(courier, "bank_code", None)
        bank_agency = getattr(courier, "bank_agency", None)
        bank_account = getattr(courier, "bank_account", None)
        bank_digit = getattr(courier, "bank_account_digit", None)
        bank_type = getattr(courier, "bank_account_type", None) or "CC"
        if bank_code and bank_agency and bank_account:
            payload["BankData"] = {
                "Bank": {"Code": bank_code},
                "AccountType": {"Code": bank_type},
                "BankAgency": bank_agency,
                "BankAgencyDigit": "",
                "BankAccount": bank_account,
                "BankAccountDigit": bank_digit or "0",
            }

        import structlog as _sl
        _sl.get_logger("payments.subaccount").info(
            "safe2pay_subaccount_create", identity_prefix=identity[:3] if identity else ""
        )

        data = await self._call_safe2pay(
            f"{self._api_url}/v2/marketplace/add",
            payload,
            headers=self._marketplace_headers(),
        )
        return {
            "recipient_id": str(data.get("Id", "")),
            "token": str(data.get("Token", "")),
        }

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
        """Transfere da conta autenticada (self._api_key, quem perde o dinheiro) para
        a subconta `recipient` (courier.s2p_recipient_id — Id numérico da subconta).

        Contrato real confirmado com a Safe2Pay: `POST {payment_url}/v2/InternalTransfer`.
        A resposta de sucesso só traz `{"ResponseDetail": {"Message": "..."}, "HasError":
        false}` — sem id de transação — então `reference` (nossa própria chave de
        idempotência, ex. "dlv_123") é o que persistimos como transaction_id.
        """
        await self._call_safe2pay(
            f"{self._payment_url}/v2/InternalTransfer",
            {
                "IdReceiver": int(recipient),
                "IdentificationDebit": f"Repasse {reference}",
                "IdentificationCredit": f"Recebimento {reference}",
                "Amount": amount_cents / 100,
            },
        )
        return PayoutResult(transaction_id=reference, status="paid")
