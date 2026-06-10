"""Adapter contract tests (Gate 5) — parse captured fixtures, NO network.

Validates the real adapters' response mapping against the fixtures captured in
T-13 (resolves the LOW-confidence items A1/A2/A3 from RESEARCH). The HTTP call
itself is never made; we exercise the parser/contract directly.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.integrations.geocoding import GeocodingHttpAdapter
from app.integrations.receita import ReceitaHttpAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict | list:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_receita_parses_minhareceita_ativa() -> None:
    result = ReceitaHttpAdapter._parse(_load("receita_minhareceita_ativa.json"))
    assert result.situacao == "ativa"
    assert result.razao_social == "EMPRESA EXEMPLO LTDA"


def test_receita_parses_brasilapi_ativa() -> None:
    result = ReceitaHttpAdapter._parse(_load("receita_brasilapi_ativa.json"))
    assert result.situacao == "ativa"


def test_receita_parses_inativa() -> None:
    result = ReceitaHttpAdapter._parse(_load("receita_inativa.json"))
    assert result.situacao != "ativa"


def test_geocoding_nominatim_contract_shape() -> None:
    payload = _load("geocoding_nominatim_padua.json")
    assert isinstance(payload, list) and payload
    first = payload[0]
    # The adapter reads `lat`/`lon` strings — assert the captured contract holds.
    assert float(first["lat"]) == -21.541
    assert float(first["lon"]) == -42.043


def test_geocoding_adapter_is_ssrf_guarded() -> None:
    # The geocoding adapter must carry an allowlist (SSRF — TH-02). A bare
    # construction without the configured host would never reach a private IP.
    adapter = GeocodingHttpAdapter(
        base_url="https://nominatim.openstreetmap.org", allowlist={"nominatim.openstreetmap.org"}
    )
    assert "nominatim.openstreetmap.org" in adapter._allowlist
