"""LLM factory — Stub in {dev, test} or when `llm_provider='stub'`, Claude otherwise.

INFRA ONLY (T-02): the M1 pilot leaves `llm_provider='stub'` (config default), so no
AI is ever wired and no API key is needed. A v1.1 deploy flips it to 'claude' and sets
ANTHROPIC_API_KEY (a secret, env-only — TH-01). The factory builds an `LLMRouter` ready
to be injected into a future feature; nothing constructs it in M1.
"""

from __future__ import annotations

from app.ai.provider import LLMProvider
from app.ai.router import LLMRouter
from app.ai.stub import StubProvider
from app.core.config import settings

_STUB_ENVS = {"dev", "test"}


def _use_stub() -> bool:
    """Stub unless explicitly 'claude' in a non-stub environment with a key set."""
    if settings.environment in _STUB_ENVS:
        return True
    if settings.llm_provider != "claude":
        return True
    return not settings.anthropic_api_key


def get_llm_provider() -> LLMProvider:
    """Return the deterministic Stub (dev/test/M1) or the Claude adapter (v1.1)."""
    if _use_stub():
        return StubProvider()
    from app.ai.claude import ClaudeAdapter

    # `anthropic_api_key` is guaranteed non-None here by `_use_stub`.
    assert settings.anthropic_api_key is not None
    return ClaudeAdapter(api_key=settings.anthropic_api_key)


def get_llm_router() -> LLMRouter:
    """Build the router with the configured provider + per-task default models (D-03)."""
    return LLMRouter(
        provider=get_llm_provider(),
        model_reasoning=settings.llm_model_reasoning,
        model_bulk=settings.llm_model_bulk,
    )
