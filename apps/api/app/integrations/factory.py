"""Adapter factory — Stub in {dev, test}, real httpx impl otherwise (Pitfall 1).

The whole point: the test suite and local dev NEVER touch the network. Production
/ staging wire the real adapters with allowlists derived from settings.
"""

from __future__ import annotations

from app.core.config import settings
from app.integrations.base import EmailPort, GeocodingPort, ReceitaPort, SmsPort
from app.integrations.email import EmailSesAdapter
from app.integrations.email_stub import EmailStubAdapter
from app.integrations.geocoding import GeocodingHttpAdapter
from app.integrations.geocoding_stub import GeocodingStubAdapter
from app.integrations.receita import ReceitaHttpAdapter
from app.integrations.receita_stub import ReceitaStubAdapter
from app.integrations.sms import SmsHttpAdapter
from app.integrations.sms_stub import SmsStubAdapter

_STUB_ENVS = {"dev", "test"}


def _hosts(raw: str) -> set[str]:
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def _use_stub() -> bool:
    return settings.environment in _STUB_ENVS


def get_receita_adapter() -> ReceitaPort:
    if _use_stub():
        return ReceitaStubAdapter(scenario="ativa")
    return ReceitaHttpAdapter(
        base_url=settings.receita_base_url,
        brasilapi_url=settings.receita_brasilapi_url,
        allowlist=_hosts(settings.receita_allowlist_hosts),
    )


def get_sms_adapter() -> SmsPort:
    if _use_stub():
        return SmsStubAdapter()
    return SmsHttpAdapter(
        zenvia_url=settings.sms_zenvia_url,
        zenvia_token=settings.sms_zenvia_token,
        twilio_url=settings.sms_twilio_url,
        twilio_token=settings.sms_twilio_token,
        allowlist=_hosts(settings.sms_allowlist_hosts),
    )


def get_email_adapter() -> EmailPort:
    if _use_stub():
        return EmailStubAdapter()
    return EmailSesAdapter(
        send_url=settings.ses_send_url,
        api_token=settings.ses_api_token,
        allowlist=_hosts(settings.ses_allowlist_hosts),
    )


def get_geocoding_adapter() -> GeocodingPort:
    if _use_stub():
        return GeocodingStubAdapter(scenario="padua")
    return GeocodingHttpAdapter(
        base_url=settings.geocoding_base_url,
        allowlist=_hosts(settings.geocoding_allowlist_hosts),
    )
