"""ClaudeAdapter — Anthropic SDK backend (Phase 14 — T-02 / D-03).

INFRA ONLY: this adapter is the production rail for the v1.1 AI features; nothing
in the M1 pilot constructs it (the factory returns the StubProvider). The
`anthropic` SDK is imported LAZILY inside `__init__` — mirroring the integrations
adapters (`import anthropic` inside the constructor) — so this module imports cleanly
WITHOUT the SDK installed and the test suite never needs it (the SDK is a v1.1
dependency, tracked as TD-14-01).

Security (TH-01): the API key is read from settings/secret, passed only to the SDK
client, and NEVER logged or returned. The adapter never raises to the router — on any
error it returns `ok=False` + `error_kind` (skill §6 fallback).
"""

from __future__ import annotations

import time

import structlog

from app.ai.provider import LLMResult

logger = structlog.get_logger("ai.claude")


class ClaudeAdapter:
    """Anthropic Claude provider via the `anthropic` SDK (lazy import)."""

    name = "claude"

    def __init__(self, *, api_key: str) -> None:
        # Lazy import: the SDK is a v1.1 dependency (TD-14-01); this module must
        # import without it. The key is held only by the SDK client (TH-01).
        import anthropic  # pyright: ignore[reportMissingImports]

        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResult:
        """Call Claude; never raise — degrade to ok=False on any failure (skill §6)."""
        start = time.perf_counter()
        try:
            resp = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            return LLMResult(
                content=resp.content[0].text,
                provider=self.name,
                model=model,
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens,
                latency_ms=latency_ms,
            )
        except Exception as exc:  # noqa: BLE001 — degrade, never raise (skill §6)
            latency_ms = int((time.perf_counter() - start) * 1000)
            # No PII, no key — only the failure shape (TH-01 / TH-03 / A09).
            logger.warning("ai.claude.failed", error=type(exc).__name__)
            return LLMResult(
                content="",
                provider=self.name,
                model=model,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                ok=False,
                error_kind=type(exc).__name__,
            )
