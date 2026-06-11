"""LLM infrastructure (Phase 14 — T-02 / REQ-053 / D-03). INFRA ONLY, no AI feature in M1.

The plugable rail for v1.1 AI features:
- `provider.LLMProvider` (Protocol) + `LLMResult` + `TaskClass`;
- `stub.StubProvider` (deterministic, dev/test) and `claude.ClaudeAdapter` (SDK, v1.1);
- `router.LLMRouter` — selects provider/model per task and records `ai_usage_log`;
- `factory.get_llm_router` — Stub in dev/test/M1, Claude in v1.1.

NO endpoint or AI feature is wired in the M1 pilot — only the rail + its usage log.
"""

from __future__ import annotations

from app.ai.factory import get_llm_provider, get_llm_router
from app.ai.provider import LLMProvider, LLMResult, TaskClass
from app.ai.router import LLMRouter

__all__ = [
    "LLMProvider",
    "LLMResult",
    "LLMRouter",
    "TaskClass",
    "get_llm_provider",
    "get_llm_router",
]
