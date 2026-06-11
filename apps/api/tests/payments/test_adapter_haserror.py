"""Safe2PayHttpAdapter: HasError on HTTP 200 raises; SSRF blocked; Stub is offline.

Skill safe2pay-escrow-br A2: HTTP 200 ≠ success — `_call_safe2pay` ALWAYS checks
`HasError`. owasp A10: `assert_safe_url` rejects a non-allowlisted host (TH-L).
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_call_safe2pay_haserror_raises(monkeypatch) -> None:
    from app.payments.errors import PaymentGatewayError
    from app.payments.safe2pay_adapter import Safe2PayHttpAdapter

    adapter = Safe2PayHttpAdapter(
        api_key="k",
        payment_url="https://payment.safe2pay.example",
        api_url="https://api.safe2pay.example",
        services_url="https://services.safe2pay.example",
        allowlist={"payment.safe2pay.example", "api.safe2pay.example", "services.safe2pay.example"},
    )

    class _Resp:
        status_code = 200

        def raise_for_status(self) -> None:  # noqa: D401
            return None

        def json(self) -> dict:
            return {"HasError": True, "ErrorCode": "40012", "Error": "valor abaixo do mínimo"}

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            return _Resp()

    monkeypatch.setattr("app.payments.safe2pay_adapter.build_client", lambda *a, **k: _Client())
    with pytest.raises(PaymentGatewayError):
        await adapter._call_safe2pay("https://payment.safe2pay.example/v2/Payment", {"Amount": 0.5})


@pytest.mark.asyncio
async def test_ssrf_rejects_non_allowlisted_host() -> None:
    from app.integrations.http import SsrfBlockedError
    from app.payments.safe2pay_adapter import Safe2PayHttpAdapter

    adapter = Safe2PayHttpAdapter(
        api_key="k",
        payment_url="https://payment.safe2pay.example",
        api_url="https://api.safe2pay.example",
        services_url="https://services.safe2pay.example",
        allowlist={"payment.safe2pay.example"},
    )
    with pytest.raises(SsrfBlockedError):
        await adapter._call_safe2pay("http://169.254.169.254/latest/meta-data", {})


@pytest.mark.asyncio
async def test_stub_is_offline_and_deterministic(payment_stub) -> None:
    from app.payments.port import Customer

    customer = Customer(name="Loja", document="12345678000190", email="a@b.com")
    result = await payment_stub.charge_with_token(
        token="tok_x", amount_cents=9990, reference="ref_1", customer=customer
    )
    assert result.transaction_id  # deterministic id assigned
    assert result.status == "paid"


@pytest.mark.asyncio
async def test_factory_returns_stub_in_test_env() -> None:
    from app.payments.factory import get_payment_adapter
    from app.payments.safe2pay_stub import PaymentStubAdapter

    adapter = get_payment_adapter()
    assert isinstance(adapter, PaymentStubAdapter)
