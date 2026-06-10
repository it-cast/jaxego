"""ReceitaStubAdapter — dev/test only; NEVER touches the network.

Scenario-driven so tests can drive E1 ("inativa") and E4 ("down"). The happy
path ("ativa") returns a deterministic fixture-shaped result.
"""

from __future__ import annotations

from app.integrations.base import ReceitaResult


class ReceitaStubAdapter:
    """Configurable CNPJ lookup stub (no network)."""

    def __init__(self, scenario: str = "ativa") -> None:
        self._scenario = scenario

    async def consultar_cnpj(self, cnpj: str) -> ReceitaResult | None:
        if self._scenario == "down":
            return None  # provider unavailable -> E4 (pending_validation)
        if self._scenario in {"inativa", "inexistente"}:
            return ReceitaResult(situacao=self._scenario, razao_social=None, cnaes=[])
        return ReceitaResult(situacao="ativa", razao_social="STUB COMERCIO LTDA", cnaes=["4712100"])
