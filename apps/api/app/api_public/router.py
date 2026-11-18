"""/v1/deliveries (public) — API-key auth + 24h idempotency + per-key rate limit.

# público: this router is authenticated by an AREA API KEY (`api_key_scope`), not a
user session. It resolves the target store within the key's area (404 cross-area —
TH-03), REQUIRES an `Idempotency-Key` header (D-04 — different from the optional
internal one), and is rate-limited per API key (429 + `Retry-After` — D-05). It calls
the SAME `create_delivery` service as the internal router (zero duplication) and
`commit()`s here (the phase pattern). The request body carries recipient PII and is
NEVER logged (TH-09).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys.dependencies import ApiKeyScopeDep, require_scope
from app.api_public import service
from app.api_public.schemas import (
    PublicCancelBody,
    PublicCreateDeliveryBody,
    PublicCreateMerchantBody,
    PublicCreateMerchantOut,
    PublicMerchantAccessBody,
    PublicMerchantAccessOut,
    PublicDeliveryDetail,
    PublicDeliveryResponse,
    PublicMerchantOut,
    PublicQuoteOut,
    ResolveMerchantBody,
)
from app.core.exceptions import ValidationAppError
from app.core.ratelimit import SlidingWindowLimiter
from app.db.session import get_session

router = APIRouter(prefix="/deliveries", tags=["public-deliveries"])
# Vínculo da loja e cotação (integração Menu Certo) — montado também em /v1/public
extras_router = APIRouter(tags=["public-deliveries"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Per-API-key create limit (D-05 / TH-08). 60/min per key — generous for an
# integrator batch while blocking flood/abuse. In-process limiter (pilot scale).
_WINDOW = timedelta(minutes=1)
public_create_limiter = SlidingWindowLimiter(limit=60, window=_WINDOW)
_RETRY_AFTER_SECONDS = int(_WINDOW.total_seconds())
# Leituras (detalhe, cotação, vínculo) e cancelamento: o integrador consulta as entregas
# ativas a cada minuto e a tela de cada pedido; 600/min por chave cobre com folga.
public_read_limiter = SlidingWindowLimiter(limit=600, window=_WINDOW)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=PublicDeliveryResponse)
async def create_public_delivery(
    body: PublicCreateDeliveryBody,
    request: Request,
    response: Response,
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("deliveries:write"))],
    session: SessionDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PublicDeliveryResponse:
    """Create a delivery via the public API (F-04). Idempotency-Key is mandatory (D-04)."""
    if not idempotency_key or not idempotency_key.strip():
        # Mandatory on the public surface (unlike the internal optional header).
        raise ValidationAppError("O cabeçalho Idempotency-Key é obrigatório.")

    # Per-key rate limit → 429 with Retry-After (D-05 / TH-08).
    public_create_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)

    status_code, result, replayed = await service.create_public_delivery(
        session,
        area_id=scope.area_id,
        api_key_id=scope.api_key_id,
        idempotency_key=idempotency_key.strip(),
        body=body,
        ip=_client_ip(request),
    )
    await session.commit()

    if not replayed:
        # Kick off the cascade exactly like the internal router (enqueued, never inline).
        from app.workers.dispatch import enqueue_dispatch

        await enqueue_dispatch(result.delivery_id)

    response.status_code = status_code
    return result


@router.get("/{delivery_id}", response_model=PublicDeliveryDetail)
async def get_public_delivery(
    delivery_id: int,
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("deliveries:read"))],
    session: SessionDep,
) -> PublicDeliveryDetail:
    """Estado completo de uma entrega da área da chave (outra área = 404)."""
    public_read_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)
    return await service.delivery_detail(session, area_id=scope.area_id, delivery_id=delivery_id)


@router.post("/{delivery_id}/cancel", response_model=PublicDeliveryDetail)
async def cancel_public_delivery(
    delivery_id: int,
    body: PublicCancelBody,
    request: Request,
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("deliveries:write"))],
    session: SessionDep,
) -> PublicDeliveryDetail:
    """Cancela antes do aceite (RN-019). Depois do aceite: 422 invalid_transition."""
    public_read_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)
    delivery = await service.cancel_public_delivery(
        session,
        area_id=scope.area_id,
        delivery_id=delivery_id,
        reason=body.reason,
        ip=_client_ip(request),
    )
    await session.commit()
    # Mesmo pós-cancelamento da loja: tira as ofertas pendentes e estorna o PIX, se houver
    from app.core.redis import get_redis_client
    from app.dispatch import service as dispatch_service
    from app.workers.refund import enqueue_refund

    await dispatch_service.cancel_pending_offers(get_redis_client(), delivery_id=delivery.id)
    await enqueue_refund(delivery.id)
    return await service.delivery_detail(session, area_id=scope.area_id, delivery_id=delivery.id)


@extras_router.post("/merchants/resolve", response_model=PublicMerchantOut)
async def resolve_public_merchant(
    body: ResolveMerchantBody,
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("deliveries:read"))],
    session: SessionDep,
) -> PublicMerchantOut:
    """Acha a loja da área pelo CNPJ/CPF (vínculo da loja no integrador). Fora da área = 404."""
    public_read_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)
    return await service.resolve_merchant_by_document(
        session, area_id=scope.area_id, document=body.document
    )


@extras_router.get("/quote", response_model=PublicQuoteOut)
async def public_quote(
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("deliveries:read"))],
    session: SessionDep,
    dropoff_neighborhood_id: Annotated[int | None, Query(ge=1)] = None,
    dropoff_neighborhood_name: Annotated[str | None, Query(max_length=120)] = None,
    dropoff_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    dropoff_lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    dropoff_address: Annotated[str | None, Query(max_length=255)] = None,
    dropoff_number: Annotated[str | None, Query(max_length=20)] = None,
    cep: Annotated[str | None, Query(max_length=9)] = None,
) -> PublicQuoteOut:
    """Entregadores que atendem agora o destino e a faixa de preço (sem criar nada)."""
    public_read_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)
    if dropoff_neighborhood_id is None and not (dropoff_neighborhood_name or "").strip():
        raise ValidationAppError("Informe dropoff_neighborhood_id ou dropoff_neighborhood_name.")
    return await service.quote(
        session,
        area_id=scope.area_id,
        nbhd_id=dropoff_neighborhood_id,
        nbhd_name=dropoff_neighborhood_name,
        lat=dropoff_lat if dropoff_lng is not None else None,
        lng=dropoff_lng if dropoff_lat is not None else None,
        address=dropoff_address,
        number=dropoff_number,
        cep=cep,
    )


# Cadastro de loja pelo integrador: raro (ação da equipe Menu Certo) — 20/min por chave.
public_merchant_limiter = SlidingWindowLimiter(limit=20, window=_WINDOW)


@extras_router.post("/merchants", response_model=PublicCreateMerchantOut, status_code=201)
async def create_public_merchant(
    body: PublicCreateMerchantBody,
    request: Request,
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("merchants:write"))],
    session: SessionDep,
) -> PublicCreateMerchantOut:
    """Cadastra a loja na área da chave, ativa e no plano pago pelo integrador."""
    from app.integrations.factory import get_geocoding_adapter, get_receita_adapter

    public_merchant_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)
    out = await service.create_merchant_by_integrator(
        session,
        area_id=scope.area_id,
        body=body,
        receita=get_receita_adapter(),
        geocoding=get_geocoding_adapter(),
        ip=_client_ip(request),
        api_key_id=scope.api_key_id,
    )
    await session.commit()
    return out


@extras_router.post("/merchants/{merchant_id}/access", response_model=PublicMerchantAccessOut)
async def set_public_merchant_access(
    merchant_id: int,
    body: PublicMerchantAccessBody,
    request: Request,
    scope: Annotated[ApiKeyScopeDep, Depends(require_scope("merchants:write"))],
    session: SessionDep,
) -> PublicMerchantAccessOut:
    """Liga (active) ou desliga (cancelado) o acesso da loja da área. Fora da área = 404."""
    public_merchant_limiter.check(f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS)
    out = await service.set_merchant_access(
        session,
        area_id=scope.area_id,
        merchant_id=merchant_id,
        active=body.active,
        ip=_client_ip(request),
        api_key_id=scope.api_key_id,
    )
    await session.commit()
    return out


__all__ = [
    "router",
    "extras_router",
    "public_create_limiter",
    "public_merchant_limiter",
    "public_read_limiter",
]
