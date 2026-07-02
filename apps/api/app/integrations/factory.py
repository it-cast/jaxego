"""Adapter factory — Stub in {dev, test}, real httpx impl otherwise (Pitfall 1).

The whole point: the test suite and local dev NEVER touch the network. Production
/ staging wire the real adapters with allowlists derived from settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir

from app.core.config import settings
from app.integrations.base import (
    EmailPort,
    GeocodingPort,
    PushPort,
    ReceitaPort,
    RoutingPort,
    SmsPort,
    StoragePort,
)
from app.integrations.email import EmailSesAdapter
from app.integrations.email_stub import EmailStubAdapter
from app.integrations.geocoding import GeocodingHttpAdapter
from app.integrations.geocoding_mapbox import MapboxGeocodingAdapter
from app.integrations.geocoding_stub import GeocodingStubAdapter
from app.integrations.push import PushVapidAdapter
from app.integrations.push_stub import PushStubAdapter
from app.integrations.receita import ReceitaHttpAdapter
from app.integrations.receita_stub import ReceitaStubAdapter
from app.integrations.routing import RoutingHttpAdapter
from app.integrations.routing_stub import RoutingStubAdapter
from app.integrations.sms import SmsHttpAdapter
from app.integrations.sms_stub import SmsStubAdapter
from app.integrations.storage import StorageB2Adapter
from app.integrations.storage_stub import StorageStubAdapter

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
    if settings.mapbox_token:
        return MapboxGeocodingAdapter(token=settings.mapbox_token)
    return GeocodingHttpAdapter(
        base_url=settings.geocoding_base_url,
        allowlist=_hosts(settings.geocoding_allowlist_hosts),
    )


@lru_cache
def _stub_storage() -> StorageStubAdapter:
    """A process-wide stub rooted in the OS temp dir (dev only; tests inject own)."""
    base_url = "http://localhost:8000" if settings.environment == "dev" else None
    return StorageStubAdapter(root=Path(gettempdir()) / "jaxego-b2-stub", base_url=base_url)


def get_storage_adapter() -> StoragePort:
    """KYC document storage: Stub in dev/test (FS temp, no network), B2 otherwise.

    The B2 secrets (key_id/app_key) are required for the real adapter; if they are
    absent in a non-stub environment the StorageB2Adapter is constructed with empty
    strings only as a last resort — staging/production MUST set them (Gate 8).
    """
    if _use_stub():
        return _stub_storage()
    return StorageB2Adapter(
        endpoint_url=settings.b2_endpoint_url,
        region=settings.b2_region,
        key_id=settings.b2_key_id or "",
        app_key=settings.b2_app_key or "",
        bucket=settings.b2_kyc_bucket,
        allowlist=_hosts(settings.b2_allowlist_hosts),
    )


def get_routing_adapter() -> RoutingPort:
    """OSRM routing: haversine Stub in dev/test, OSRM httpx otherwise (degrades)."""
    if _use_stub():
        return RoutingStubAdapter()
    return RoutingHttpAdapter(
        base_url=settings.osrm_base_url,
        profile=settings.osrm_profile,
        allowlist=_hosts(settings.osrm_allowlist_hosts),
    )


def get_push_adapter() -> PushPort:
    """Web Push: in-memory Stub in dev/test, VAPID (pywebpush) otherwise."""
    if _use_stub():
        return PushStubAdapter()
    return PushVapidAdapter(
        private_key=settings.vapid_private_key,
        public_key=settings.vapid_public_key,
        claim_sub=settings.vapid_claim_sub,
    )
