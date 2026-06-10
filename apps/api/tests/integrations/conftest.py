"""Fixtures for the external-integration adapters (Phase 4).

Every test here uses the STUB adapters — they NEVER touch the network (Pitfall 1
/ Gate 5). The stubs are configurable by scenario so a test can drive E1
(``"inativa"``), E4 (``"down"``) or the happy path (``"ativa"``).
"""

from __future__ import annotations

import pytest

from app.integrations.email_stub import EmailStubAdapter
from app.integrations.geocoding_stub import GeocodingStubAdapter
from app.integrations.receita_stub import ReceitaStubAdapter
from app.integrations.sms_stub import SmsStubAdapter


@pytest.fixture
def receita_stub_ativa() -> ReceitaStubAdapter:
    return ReceitaStubAdapter(scenario="ativa")


@pytest.fixture
def receita_stub_inativa() -> ReceitaStubAdapter:
    return ReceitaStubAdapter(scenario="inativa")


@pytest.fixture
def receita_stub_down() -> ReceitaStubAdapter:
    return ReceitaStubAdapter(scenario="down")


@pytest.fixture
def sms_stub() -> SmsStubAdapter:
    return SmsStubAdapter()


@pytest.fixture
def email_stub() -> EmailStubAdapter:
    return EmailStubAdapter()


@pytest.fixture
def geocoding_stub_padua() -> GeocodingStubAdapter:
    """Geocoder that always resolves inside the Pádua area."""
    return GeocodingStubAdapter(scenario="padua")


@pytest.fixture
def geocoding_stub_fora() -> GeocodingStubAdapter:
    """Geocoder that resolves to a point with no covering area (empty state)."""
    return GeocodingStubAdapter(scenario="fora")
