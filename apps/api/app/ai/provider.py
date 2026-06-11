"""LLM provider Protocol + result dataclass (Phase 14 — T-02 / REQ-053 / D-03).

INFRA ONLY: this is the plugable rail for the v1.1 AI features — there is NO AI
feature or endpoint wired in the M1 pilot. The router depends on this `Protocol`,
never on a concrete SDK (skill llm-integration-patterns §5: "Não dependa de SDK de
um provider. Abstraia."), so the test suite injects the deterministic `StubProvider`
with no network and no API key.

PII discipline (TH-03 / skill §10/§15): the prompt the caller passes MUST already be
free of personal data; the provider returns only the completion text + token/latency
metadata. NOTHING here logs the raw prompt or any PII.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TaskClass(str, Enum):
    """The class of work — drives model selection in the router (D-03).

    REASONING → the most capable family (opus); BULK → the cheap/high-volume family
    (haiku). Both default models are parametrised in settings, never hardcoded here.
    """

    REASONING = "reasoning"
    BULK = "bulk"


@dataclass(frozen=True)
class LLMResult:
    """Outcome of one completion. Carries ONLY metadata — never PII (TH-03).

    `ok=False` + `error_kind` means the call failed and `content` is empty; the
    router still records the attempt in `ai_usage_log` (the rail is observable from
    day one even though no feature consumes it in M1).
    """

    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    ok: bool = True
    error_kind: str | None = None


class LLMProvider(Protocol):
    """A completion backend. The router calls `complete`; impls never raise to it.

    `system` + `user` are the (PII-free) prompt parts. The impl returns an
    `LLMResult`; on failure it returns `ok=False` with an `error_kind` rather than
    raising, so the router can record the attempt and degrade gracefully (skill §6).
    """

    name: str

    async def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResult: ...
