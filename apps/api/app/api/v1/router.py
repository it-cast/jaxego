"""Aggregate router for versioned domain endpoints (/v1).

Thin: only wires sub-routers. No domain endpoints exist yet (Phase 2+).
The health probe is mounted at the root (`/health`), not here — see app.main.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.auth.router import router as auth_router

api_router = APIRouter()

# Phase 2 domain sub-routers.
api_router.include_router(auth_router)
