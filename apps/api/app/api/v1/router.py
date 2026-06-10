"""Aggregate router for versioned domain endpoints (/v1).

Thin: only wires sub-routers. No domain endpoints exist yet (Phase 2+).
The health probe is mounted at the root (`/health`), not here — see app.main.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.areas.router import router as areas_router
from app.auth.router import router as auth_router
from app.couriers.router import admin_router as couriers_admin_router
from app.couriers.router import router as couriers_router
from app.merchants.router import interest_router
from app.merchants.router import router as merchants_router
from app.neighborhoods.router import router as neighborhoods_router
from app.plans.router import router as plans_router

api_router = APIRouter()

# Phase 2 domain sub-routers.
api_router.include_router(auth_router)
api_router.include_router(areas_router)

# Phase 4 domain sub-routers (F-01).
api_router.include_router(merchants_router)
api_router.include_router(plans_router)
api_router.include_router(interest_router)

# Phase 5 domain sub-routers (F-02).
api_router.include_router(couriers_router)
api_router.include_router(couriers_admin_router)

# Phase 6 domain sub-routers (área operável).
api_router.include_router(neighborhoods_router)
