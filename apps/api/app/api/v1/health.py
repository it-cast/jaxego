"""Health/readiness probe — mounted at the root as GET /health.

Placeholder during T-02 (skeleton). T-05 wires the real MySQL `SELECT 1` and
Redis `ping()` checks. Kept at the root (no /v1 prefix) per Docker/Nginx/k8s
convention — this is the path exercised by HEALTHCHECK and CI.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness skeleton — replaced by full readiness check in T-05."""
    return {"status": "ok"}
