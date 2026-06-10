"""Health/readiness probe — mounted at the root as GET /health.

Exposed at the root (no /v1 prefix): the Docker/Nginx/k8s convention and the
exact path exercised by the container HEALTHCHECK and by CI (`curl -f /health`).

Checks MySQL (`SELECT 1`) and Redis (`ping()`). Returns
`{ status, db, redis, version }`: 200 when both are ok, 503 otherwise. No N+1,
no domain query, no PII.
"""

from __future__ import annotations

from typing import Literal

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

logger = structlog.get_logger("health")

router = APIRouter(tags=["health"])

ComponentStatus = Literal["ok", "down"]


class HealthRead(BaseModel):
    """Health response contract: { status, db, redis, version }."""

    model_config = ConfigDict(from_attributes=True)

    status: Literal["ok", "degraded"]
    db: ComponentStatus
    redis: ComponentStatus
    version: str


async def check_db() -> ComponentStatus:
    """Run `SELECT 1` against MySQL. Returns 'ok' or 'down'."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        logger.warning("health_db_check_failed")
        return "down"


async def check_redis() -> ComponentStatus:
    """Ping Redis. Returns 'ok' or 'down'."""
    client = aioredis.from_url(settings.redis_url)
    try:
        await client.ping()
        return "ok"
    except Exception:
        logger.warning("health_redis_check_failed")
        return "down"
    finally:
        await client.aclose()


@router.get("/health", response_model=HealthRead)
async def health() -> JSONResponse:
    """Readiness probe checking MySQL and Redis."""
    db_status = await check_db()
    redis_status = await check_redis()
    healthy = db_status == "ok" and redis_status == "ok"

    payload = HealthRead(
        status="ok" if healthy else "degraded",
        db=db_status,
        redis=redis_status,
        version=settings.app_version,
    )
    return JSONResponse(
        status_code=200 if healthy else 503,
        content=payload.model_dump(),
    )
