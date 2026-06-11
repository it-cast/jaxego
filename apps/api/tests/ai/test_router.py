"""LLM infra (Phase 14 — T-02 / REQ-053): the Stub works and ai_usage_log is written.

INFRA ONLY: there is NO AI endpoint in M1. These tests prove the rail:
- the StubProvider returns a deterministic completion (no network, no key);
- the LLMRouter selects the model per task class (REASONING → opus, BULK → haiku);
- every call records ONE `ai_usage_log` row with token/cost/latency metadata and NO
  PII (no prompt, no completion, no key stored);
- a failing provider still records the attempt with ok=False + error_kind.
"""

from __future__ import annotations

import pytest
from app.ai.factory import get_llm_router
from app.ai.models import AiUsageLog
from app.ai.provider import LLMResult, TaskClass
from app.ai.router import LLMRouter, estimate_cost_cents
from app.ai.stub import StubProvider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_stub_provider_deterministic() -> None:
    stub = StubProvider()
    r1 = await stub.complete(system="sys", user="hello", model="claude-haiku-4-5")
    r2 = await stub.complete(system="sys", user="hello", model="claude-haiku-4-5")
    assert r1.ok is True
    assert r1.content == r2.content == "[stub-completion]"
    assert r1.input_tokens == r2.input_tokens
    assert r1.provider == "stub"


@pytest.mark.asyncio
async def test_router_records_usage_log(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    router = LLMRouter(
        provider=StubProvider(),
        model_reasoning="claude-opus-4-5",
        model_bulk="claude-haiku-4-5",
    )
    async with session_factory() as s:
        result = await router.complete(
            s,
            task="eta_predict",
            task_class=TaskClass.BULK,
            system="you are a router",
            user="estimate this trip",  # PII-free by contract
            request_id="req-123",
        )
        await s.commit()

    assert result.ok is True
    # BULK → the bulk (haiku) model was selected.
    assert result.model == "claude-haiku-4-5"

    async with session_factory() as s:
        rows = (await s.execute(select(AiUsageLog))).scalars().all()
        assert len(rows) == 1
        row = rows[0]
        assert row.provider == "stub"
        assert row.model == "claude-haiku-4-5"
        assert row.task == "eta_predict"
        assert row.input_tokens > 0
        assert row.request_id == "req-123"
        assert row.ok is True
        assert row.error_kind is None
        assert row.created_at is not None


@pytest.mark.asyncio
async def test_router_selects_reasoning_model(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    router = LLMRouter(
        provider=StubProvider(),
        model_reasoning="claude-opus-4-5",
        model_bulk="claude-haiku-4-5",
    )
    async with session_factory() as s:
        result = await router.complete(
            s,
            task="fraud_reason",
            task_class=TaskClass.REASONING,
            system="s",
            user="u",
        )
        await s.commit()
    assert result.model == "claude-opus-4-5"


@pytest.mark.asyncio
async def test_router_records_failed_attempt(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """A provider that degrades (ok=False) is still recorded for observability."""

    class FailingProvider:
        name = "stub"

        async def complete(self, **_kwargs: object) -> LLMResult:
            return LLMResult(
                content="",
                provider=self.name,
                model="claude-haiku-4-5",
                input_tokens=0,
                output_tokens=0,
                latency_ms=12,
                ok=False,
                error_kind="TimeoutError",
            )

    router = LLMRouter(
        provider=FailingProvider(),
        model_reasoning="claude-opus-4-5",
        model_bulk="claude-haiku-4-5",
    )
    async with session_factory() as s:
        result = await router.complete(
            s, task="bulk_task", task_class=TaskClass.BULK, system="s", user="u"
        )
        await s.commit()

    assert result.ok is False
    async with session_factory() as s:
        row = (await s.execute(select(AiUsageLog))).scalars().one()
        assert row.ok is False
        assert row.error_kind == "TimeoutError"
        assert row.cost_cents == 0


def test_factory_returns_stub_in_test_env() -> None:
    """In the test environment the factory must NEVER wire a real provider (TH-01)."""
    router = get_llm_router()
    assert isinstance(router, LLMRouter)
    # The injected provider is the deterministic Stub (no network, no key).
    assert router._provider.name == "stub"  # noqa: SLF001 (test asserts wiring)


def test_cost_estimate_by_family() -> None:
    # opus: $15/MTok in, $75/MTok out → 1M in + 1M out = 1500 + 7500 cents.
    assert estimate_cost_cents("claude-opus-4-5", input_tokens=1_000_000, output_tokens=0) == 1500
    assert estimate_cost_cents("claude-haiku-4-5", input_tokens=0, output_tokens=1_000_000) == 500
    # Unknown model → 0 (the rail still records tokens).
    assert estimate_cost_cents("some-future-model", input_tokens=1_000_000, output_tokens=0) == 0
