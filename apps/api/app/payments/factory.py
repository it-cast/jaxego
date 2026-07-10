"""Payment adapter factory — Stub in {dev, test}, real httpx impl otherwise (D-09).

Same pattern as `app/integrations/factory.py`: the test suite and local dev NEVER touch
the network nor Safe2Pay sandbox. Production/staging wire the real adapter with the
allowlist + secrets from settings (Gate 8 — a missing api_key in production is a deploy
problem, not a silent fallback).
"""

from __future__ import annotations

from app.core.config import settings
from app.payments.port import PaymentPort
from app.payments.safe2pay_adapter import Safe2PayHttpAdapter
from app.payments.safe2pay_stub import PaymentStubAdapter

_STUB_ENVS = {"dev", "test"}


def _hosts(raw: str) -> set[str]:
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def _use_stub() -> bool:
    return settings.environment in _STUB_ENVS


def get_payment_adapter() -> PaymentPort:
    """Return the Stub in dev/test, the real Safe2Pay httpx adapter otherwise."""
    if _use_stub():
        return PaymentStubAdapter(scenario="approved")
    return Safe2PayHttpAdapter(
        api_key=settings.safe2pay_token,
        payment_url=settings.safe2pay_payment_url,
        api_url=settings.safe2pay_api_url,
        services_url=settings.safe2pay_services_url,
        allowlist=_hosts(settings.safe2pay_allowlist_hosts),
        sandbox=settings.safe2pay_sandbox,
        jaxego_recipient=settings.safe2pay_jaxego_recipient,
    )
