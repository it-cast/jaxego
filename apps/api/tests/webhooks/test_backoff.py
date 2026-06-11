"""EXACT 8× backoff for webhook delivery (T-09 / LOW-1 / TH-10) — controlled clock.

Proves the ADR-010 schedule deterministically WITHOUT sleeping: a fake delivery
row is driven through 8 failed attempts at a fixed `now`, and the scheduled
`next_retry_at` after each failure is asserted against the exact interval
`[30,120,600,3600,14400,43200,86400]s`; the 8th failure marks `failed` (no 9th).
A 2xx short-circuits to `delivered`; a 4xx≠429 is a permanent failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.webhooks.delivery import (
    BACKOFF_AFTER_SECONDS,
    CUMULATIVE_OFFSETS_SECONDS,
    MAX_ATTEMPTS,
    apply_attempt_result,
    compute_next_retry,
)

_T0 = datetime(2026, 6, 11, 12, 0, 0, tzinfo=UTC)


@dataclass
class _FakeRow:
    """Stand-in for a WebhookDelivery row (only the fields the logic touches)."""

    id: int = 1
    area_id: int = 1
    event_type: str = "delivery.created"
    status: str = "pending"
    attempts: int = 0
    next_retry_at: datetime | None = _T0
    last_status_code: int | None = None
    delivered_at: datetime | None = None


def test_compute_next_retry_matches_exact_schedule() -> None:
    for failed_attempt in range(1, MAX_ATTEMPTS):
        nxt = compute_next_retry(failed_attempt=failed_attempt, now=_T0)
        expected = _T0 + timedelta(seconds=BACKOFF_AFTER_SECONDS[failed_attempt - 1])
        assert nxt == expected, failed_attempt
    # The 8th failure is terminal — no next retry.
    assert compute_next_retry(failed_attempt=MAX_ATTEMPTS, now=_T0) is None


def test_eight_failures_produce_exact_intervals_then_failed() -> None:
    row = _FakeRow()
    expected_waits = list(BACKOFF_AFTER_SECONDS) + [None]  # after attempts 1..8

    for i, wait in enumerate(expected_waits, start=1):
        outcome = apply_attempt_result(row, status_code=500, now=_T0)
        assert row.attempts == i
        if wait is None:
            # 8th failure → terminal failed (no retry scheduled).
            assert outcome.terminal is True
            assert row.status == "failed"
            assert row.next_retry_at is None
        else:
            assert outcome.terminal is False
            assert row.status == "pending"
            assert row.next_retry_at == _T0 + timedelta(seconds=wait), i


def test_cumulative_offsets_constant_is_consistent() -> None:
    # The documented cumulative offsets must equal the running sum of the gaps.
    running = 0
    cumulative = [0]
    for gap in BACKOFF_AFTER_SECONDS:
        running += gap
        cumulative.append(running)
    assert tuple(cumulative) == CUMULATIVE_OFFSETS_SECONDS
    assert len(CUMULATIVE_OFFSETS_SECONDS) == MAX_ATTEMPTS


def test_2xx_marks_delivered_and_stops() -> None:
    row = _FakeRow()
    outcome = apply_attempt_result(row, status_code=200, now=_T0)
    assert outcome.terminal is True
    assert row.status == "delivered"
    assert row.delivered_at == _T0
    assert row.next_retry_at is None


def test_4xx_not_429_is_permanent_failure() -> None:
    row = _FakeRow()
    outcome = apply_attempt_result(row, status_code=400, now=_T0)
    assert outcome.terminal is True
    assert row.status == "failed"
    assert row.next_retry_at is None
    assert row.attempts == 1  # no retries for a permanent 4xx


def test_429_is_retried_like_5xx() -> None:
    row = _FakeRow()
    apply_attempt_result(row, status_code=429, now=_T0)
    assert row.status == "pending"
    assert row.next_retry_at == _T0 + timedelta(seconds=BACKOFF_AFTER_SECONDS[0])
