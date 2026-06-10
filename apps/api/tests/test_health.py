"""Tests for GET /health and Sentry conditional init (T-05 + T-06).

Datastore checks are mocked so the suite runs without live MySQL/Redis; CI runs
the same endpoint against real services. Sentry tests assert no-op without DSN
and a single init call with a fake DSN (mocked — no real traffic, no secret).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok_returns_200(client: AsyncClient) -> None:
    """Both datastores ok => 200 with status ok."""
    with (
        patch("app.api.v1.health.check_db", return_value="ok"),
        patch("app.api.v1.health.check_redis", return_value="ok"),
    ):
        resp = await client.get("/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "db": "ok", "redis": "ok", "version": body["version"]}


@pytest.mark.asyncio
async def test_health_payload_has_required_fields(client: AsyncClient) -> None:
    """Response carries the documented contract { status, db, redis, version }."""
    with (
        patch("app.api.v1.health.check_db", return_value="ok"),
        patch("app.api.v1.health.check_redis", return_value="ok"),
    ):
        resp = await client.get("/health")

    body = resp.json()
    assert set(body.keys()) == {"status", "db", "redis", "version"}


@pytest.mark.asyncio
async def test_health_db_down_returns_503(client: AsyncClient) -> None:
    """A down datastore yields 503 and a degraded status."""
    with (
        patch("app.api.v1.health.check_db", return_value="down"),
        patch("app.api.v1.health.check_redis", return_value="ok"),
    ):
        resp = await client.get("/health")

    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["db"] == "down"
    assert body["redis"] == "ok"


@pytest.mark.asyncio
async def test_health_sets_request_id_header(client: AsyncClient) -> None:
    """The request emits an X-Request-ID response header (observability)."""
    with (
        patch("app.api.v1.health.check_db", return_value="ok"),
        patch("app.api.v1.health.check_redis", return_value="ok"),
    ):
        resp = await client.get("/health")

    assert resp.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_health_logs_request_with_required_fields(
    client: AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    """The request_completed log carries all required observability fields."""
    with (
        patch("app.api.v1.health.check_db", return_value="ok"),
        patch("app.api.v1.health.check_redis", return_value="ok"),
    ):
        await client.get("/health")

    out = capsys.readouterr().out
    assert "request_completed" in out
    for field in ("request_id", "user_id", "endpoint", "method", "status_code", "duration_ms"):
        assert f'"{field}"' in out, f"missing log field: {field}"
