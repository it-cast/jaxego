"""LLMRouter — selects provider/model per task and records every call (T-02 / D-03).

INFRA ONLY: the router is the single entry point for the v1.1 AI features; nothing
in the M1 pilot calls it (there is NO AI endpoint). It implements the "never call the
LLM direct from the endpoint" rule (skill §3): a future feature calls
`router.complete(task=..., system=..., user=...)`, never an SDK.

Responsibilities:
- pick the model from the task class (REASONING → opus, BULK → haiku — D-03,
  parametrised in settings);
- call the provider (which never raises — it degrades);
- record ONE `ai_usage_log` row per call (no PII, no prompt — TH-03), including a
  rough cost estimate in cents.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import AiUsageLog
from app.ai.provider import LLMProvider, LLMResult, TaskClass

logger = structlog.get_logger("ai.router")

# Rough cost per 1M tokens in USD cents (input, output) by model family (skill §6.4 /
# 2025 public pricing). Parametrised here, not in the provider; unknown models cost 0
# (the rail still records tokens). Used only for the `cost_cents` observability field.
_COST_PER_MTOK_CENTS: dict[str, tuple[int, int]] = {
    "opus": (1500, 7500),  # $15 / $75 per MTok
    "haiku": (100, 500),  # $1 / $5 per MTok
    "sonnet": (300, 1500),  # $3 / $15 per MTok
}


def _model_family(model: str) -> str | None:
    for family in _COST_PER_MTOK_CENTS:
        if family in model:
            return family
    return None


def estimate_cost_cents(model: str, *, input_tokens: int, output_tokens: int) -> int:
    """Rough USD-cent cost of a call (observability only; 0 for unknown models)."""
    family = _model_family(model)
    if family is None:
        return 0
    in_rate, out_rate = _COST_PER_MTOK_CENTS[family]
    total = (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
    return int(total)


class LLMRouter:
    """Routes a task to a provider/model and records the call in `ai_usage_log`."""

    def __init__(
        self,
        *,
        provider: LLMProvider,
        model_reasoning: str,
        model_bulk: str,
    ) -> None:
        self._provider = provider
        self._model_reasoning = model_reasoning
        self._model_bulk = model_bulk

    def _model_for(self, task_class: TaskClass) -> str:
        return self._model_reasoning if task_class == TaskClass.REASONING else self._model_bulk

    async def complete(
        self,
        session: AsyncSession,
        *,
        task: str,
        task_class: TaskClass,
        system: str,
        user: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        request_id: str | None = None,
    ) -> LLMResult:
        """Run one completion and record it. `task` is a stable label (e.g. 'eta_predict').

        `system`/`user` MUST already be PII-free (caller's contract — TH-03). The
        result is recorded in `ai_usage_log` with token/cost/latency metadata; the
        caller commits within its own transaction.
        """
        model = self._model_for(task_class)
        result = await self._provider.complete(
            system=system,
            user=user,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        cost_cents = estimate_cost_cents(
            result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
        session.add(
            AiUsageLog(
                provider=result.provider,
                model=result.model,
                task=task,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_cents=cost_cents,
                latency_ms=result.latency_ms,
                request_id=request_id,
                ok=result.ok,
                error_kind=result.error_kind,
                created_at=datetime.now(UTC),  # AWARE — TD-010
            )
        )
        await session.flush()
        # No PII, no prompt, no key — only metadata (TH-01 / TH-03 / A09).
        logger.info(
            "ai.usage",
            provider=result.provider,
            model=result.model,
            task=task,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_cents=cost_cents,
            latency_ms=result.latency_ms,
            ok=result.ok,
            error_kind=result.error_kind,
        )
        return result
