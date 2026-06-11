"""StubProvider — deterministic LLM backend for dev/test (no network, no key).

Mirrors the integrations Stub pattern (Pitfall 1): the test suite and local dev
NEVER touch the Anthropic API. The completion is a deterministic echo derived from
the prompt length, so tests can assert on a stable output and the router's
`ai_usage_log` write is exercised without any real provider.
"""

from __future__ import annotations

from app.ai.provider import LLMResult


class StubProvider:
    """Deterministic, offline LLM provider (dev/test). Returns a canned completion."""

    name = "stub"

    async def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResult:
        """Return a deterministic stub completion + synthetic token counts."""
        # Token counts are a coarse, deterministic proxy (≈ 4 chars/token) so the
        # cost/observability rail has non-zero, reproducible numbers in tests.
        input_tokens = max(1, (len(system) + len(user)) // 4)
        content = "[stub-completion]"
        output_tokens = max(1, len(content) // 4)
        return LLMResult(
            content=content,
            provider=self.name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0,
        )
