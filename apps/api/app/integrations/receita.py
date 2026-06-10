"""ReceitaHttpAdapter — minhareceita.org primary + BrasilAPI fallback (DRV-006).

Production impl. Every outbound URL passes `assert_safe_url` against the fixed
allowlist (TH-03) before connecting; redirects are disabled. A provider failure
(timeout / 5xx / network) returns None so the caller degrades to E4
(pending_validation) rather than blocking the signup.

Response shapes are normalised here; the canonical fixtures captured in T-13 live
under tests/integrations/fixtures and back the stub.
"""

from __future__ import annotations

import structlog

from app.integrations.base import ReceitaResult
from app.integrations.http import SsrfBlockedError, assert_safe_url, build_client

logger = structlog.get_logger("integrations.receita")

# BrasilAPI maps DICTs of situacao_cadastral; minhareceita returns "descricao_situacao_cadastral".
_ATIVA_TOKENS = {"ativa", "ativo", "02", "2"}


class ReceitaHttpAdapter:
    """Async CNPJ lookup with allowlist guard + provider fallback."""

    def __init__(self, *, base_url: str, brasilapi_url: str, allowlist: set[str]) -> None:
        self._base_url = base_url.rstrip("/")
        self._brasilapi_url = brasilapi_url.rstrip("/")
        self._allowlist = allowlist

    async def consultar_cnpj(self, cnpj: str) -> ReceitaResult | None:
        digits = "".join(c for c in cnpj if c.isalnum())
        for url in (f"{self._base_url}/{digits}", f"{self._brasilapi_url}/{digits}"):
            result = await self._try_provider(url)
            if result is not None:
                return result
        # Both providers unavailable -> None (E4).
        logger.warning("receita_unavailable")  # no PII (no CNPJ)
        return None

    async def _try_provider(self, url: str) -> ReceitaResult | None:
        try:
            assert_safe_url(url, allowlist=self._allowlist)
        except SsrfBlockedError:
            logger.error("receita_ssrf_blocked")
            return None
        try:
            async with build_client() as client:
                resp = await client.get(url)
            if resp.status_code != 200:
                return None
            return self._parse(resp.json())
        except Exception:  # noqa: BLE001 — provider error degrades to None (E4)
            logger.warning("receita_provider_error")
            return None

    @staticmethod
    def _parse(payload: dict) -> ReceitaResult:
        raw = (
            str(
                payload.get("descricao_situacao_cadastral")
                or payload.get("situacao_cadastral")
                or payload.get("situacao")
                or ""
            )
            .strip()
            .lower()
        )
        situacao = "ativa" if raw in _ATIVA_TOKENS else (raw or "inativa")
        razao = payload.get("razao_social") or payload.get("nome")
        cnaes_raw = payload.get("cnaes_secundarios") or []
        cnaes = [str(c.get("codigo")) for c in cnaes_raw if isinstance(c, dict)]
        return ReceitaResult(situacao=situacao, razao_social=razao, cnaes=cnaes)
