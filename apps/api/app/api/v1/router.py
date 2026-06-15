"""Aggregate router for versioned domain endpoints (/v1).

Thin: only wires sub-routers. No domain endpoints exist yet (Phase 2+).
The health probe is mounted at the root (`/health`), not here — see app.main.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.areas.admin_router import router as area_admin_router
from app.areas.router import router as areas_router
from app.auth.router import router as auth_router
from app.couriers.router import admin_router as couriers_admin_router
from app.couriers.router import router as couriers_router
from app.deliveries.router import router as deliveries_router
from app.dispatch.router import router as dispatch_router
from app.merchants.favorites import router as merchants_dispatch_router
from app.merchants.router import interest_router
from app.merchants.router import router as merchants_router
from app.neighborhoods.router import router as neighborhoods_router
from app.plans.router import router as plans_router

api_router = APIRouter()

# Phase 2 domain sub-routers.
api_router.include_router(auth_router)
api_router.include_router(areas_router)
api_router.include_router(area_admin_router)

# Phase 4 domain sub-routers (F-01).
api_router.include_router(merchants_router)
api_router.include_router(plans_router)
api_router.include_router(interest_router)

# Phase 5 domain sub-routers (F-02).
api_router.include_router(couriers_router)
api_router.include_router(couriers_admin_router)

# Phase 6 domain sub-routers (área operável).
api_router.include_router(neighborhoods_router)

# Phase 7 domain sub-routers (F-03 — criação de entrega + máquina de estados).
api_router.include_router(deliveries_router)

# Phase 8 domain sub-routers (F-05 — despacho em cascata + oferta + aceite).
api_router.include_router(dispatch_router)
api_router.include_router(merchants_dispatch_router)

# Phase 9 domain sub-routers (F-06 — comprovação, tracking público, localização).
from app.notifications.router import router as push_subscriptions_router  # noqa: E402
from app.payments_direct.router import router as payments_direct_router  # noqa: E402
from app.proofs.router import router as proofs_router  # noqa: E402
from app.tracking.locations import router as locations_router  # noqa: E402
from app.tracking.public import router as public_tracking_router  # noqa: E402

api_router.include_router(public_tracking_router)
api_router.include_router(locations_router)
api_router.include_router(proofs_router)
api_router.include_router(push_subscriptions_router)
api_router.include_router(payments_direct_router)

# Phase 10 domain sub-routers (Safe2Pay núcleo — assinatura/cobrança/estorno + webhooks).
from app.payments.router import router as payments_router  # noqa: E402
from app.payments.webhooks_router import router as payments_webhooks_router  # noqa: E402

api_router.include_router(payments_router)
api_router.include_router(payments_webhooks_router)

# Phase 12 domain sub-routers (API pública + integração Menu Certo — F-04).
# - api_public.router: POST /v1/deliveries (public, API-key auth, idempotent).
# - api_keys.admin_router: /v1/admin/areas/{area_id}/api-keys + /webhook (area admin).
from app.api_keys.admin_router import router as api_keys_admin_router  # noqa: E402
from app.api_public.router import router as public_deliveries_router  # noqa: E402

api_router.include_router(public_deliveries_router, prefix="/public")
api_router.include_router(api_keys_admin_router)

# Phase 13 domain sub-routers (governança — score, avaliações, suspensão/recurso,
# admin de plataforma). Score is read-only (TH-05); admin plataforma is TOTP-gated.
from app.platform_admin.router import router as platform_admin_router  # noqa: E402
from app.ratings.router import router as ratings_router  # noqa: E402
from app.scores.router import admin_router as scores_admin_router  # noqa: E402
from app.scores.router import router as scores_router  # noqa: E402
from app.suspensions.router import admin_router as suspensions_admin_router  # noqa: E402
from app.suspensions.router import disputes_router as disputes_admin_router  # noqa: E402

api_router.include_router(scores_router)
api_router.include_router(scores_admin_router)
api_router.include_router(ratings_router)
api_router.include_router(suspensions_admin_router)
api_router.include_router(disputes_admin_router)
api_router.include_router(platform_admin_router)

# Phase 15 domain sub-routers (financeiro back-office — fatura, saque, decisão de disputa).
# - invoices.router: /v1/invoices (loja: listar + pagar fatura) — F-03 E5 / REQ-037.
# - withdrawals.router: /v1/withdrawals (entregador: saldo + solicitar saque) — REQ-038.
# - disputes_router: /v1/platform/disputes (admin: decisão financeira) — REQ-039 (TOTP).
from app.invoices.router import router as invoices_router  # noqa: E402
from app.payments_direct.disputes_router import router as platform_disputes_router  # noqa: E402
from app.withdrawals.router import router as withdrawals_router  # noqa: E402

api_router.include_router(invoices_router)
api_router.include_router(withdrawals_router)
api_router.include_router(platform_disputes_router)
