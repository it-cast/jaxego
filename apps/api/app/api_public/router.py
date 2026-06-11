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

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys.dependencies import ApiKeyScopeDep, require_scope
from app.api_public import service
from app.api_public.schemas import PublicCreateDeliveryBody, PublicDeliveryResponse
from app.core.exceptions import ValidationAppError
from app.core.ratelimit import SlidingWindowLimiter
from app.db.session import get_session

router = APIRouter(prefix="/deliveries", tags=["public-deliveries"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Per-API-key create limit (D-05 / TH-08). 60/min per key — generous for an
# integrator batch while blocking flood/abuse. In-process limiter (pilot scale).
_WINDOW = timedelta(minutes=1)
public_create_limiter = SlidingWindowLimiter(limit=60, window=_WINDOW)
_RETRY_AFTER_SECONDS = int(_WINDOW.total_seconds())


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
    public_create_limiter.check(
        f"api_key:{scope.api_key_id}", retry_after=_RETRY_AFTER_SECONDS
    )

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


__all__ = ["router", "public_create_limiter"]
