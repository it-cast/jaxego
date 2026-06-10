"""Aggregate router for versioned domain endpoints (/v1).

Thin: only wires sub-routers. No domain endpoints exist yet (Phase 2+).
The health probe is mounted at the root (`/health`), not here — see app.main.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()

# Domain sub-routers are included here from Phase 2 onward, e.g.:
#   from app.api.v1 import users
#   api_router.include_router(users.router)
