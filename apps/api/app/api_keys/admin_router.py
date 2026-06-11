"""/v1/admin/areas/{area_id}/api-keys + /webhook — area-admin management (T-10).

Every route is gated by `require_role("admin_area")` + `area_scope`, which resolves
the path `area_id` against the admin's token scope: an area admin reaching ANOTHER
area's `area_id` gets 403 (no cross-area management — A01). The platform admin
(TOTP-enrolled by `get_current_user`) may operate cross-area. The API key SECRET is
returned ONLY on creation (D-01); the list/detail never carry it (TH-09). `commit()`
happens in the router (the phase pattern).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys import service
from app.api_keys.schemas import (
    ApiKeyListOut,
    ApiKeyOut,
    CreateApiKeyBody,
    CreateApiKeyResponse,
)
from app.auth.dependencies import AreaScopeDep, CurrentUser, ForbiddenError, require_role
from app.db.session import get_session
from app.webhooks import repo as webhook_repo
from app.webhooks import service as webhook_service
from app.webhooks.schemas import (
    ConfigureWebhookBody,
    WebhookDeliveryListOut,
    WebhookDeliveryOut,
    WebhookEndpointOut,
)

router = APIRouter(prefix="/admin/areas", tags=["admin-api-keys"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AreaAdmin = Annotated[CurrentUser, Depends(require_role("admin_area"))]


def _resolve_area(area_id: int, scope: int | None) -> int:
    """Confirm the admin may manage `area_id`.

    `area_scope` already 403s a non-platform admin whose token scope differs from the
    path `area_id`. For a platform admin (`scope is None`) we trust the path `area_id`
    (the cross-area bypass is audited at the area router; management here is explicit).
    """
    if scope is not None and scope != area_id:
        # Defence in depth — area_scope should already have raised.
        raise ForbiddenError("Acesso a outra área não permitido.")
    return area_id


def _key_out(key) -> ApiKeyOut:
    return ApiKeyOut(
        id=key.id,
        key_id=key.key_id,
        name=key.name,
        scopes=key.scopes,
        revoked=key.revoked_at is not None,
        created_at=key.created_at.isoformat() if key.created_at else None,
        last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
    )


# --- API keys ---------------------------------------------------------------
@router.post(
    "/{area_id}/api-keys",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    area_id: int,
    body: CreateApiKeyBody,
    admin: AreaAdmin,
    scope: AreaScopeDep,
    session: SessionDep,
) -> CreateApiKeyResponse:
    """Create an API key for the area. The secret is returned ONCE (D-01)."""
    resolved = _resolve_area(area_id, scope)
    api_key, token = await service.create_api_key(
        session, area_id=resolved, name=body.name, scopes=body.scopes
    )
    await session.commit()
    return CreateApiKeyResponse(
        id=api_key.id,
        key_id=api_key.key_id,
        name=api_key.name,
        scopes=api_key.scopes,
        secret=token,
    )


@router.get("/{area_id}/api-keys", response_model=ApiKeyListOut)
async def list_api_keys(
    area_id: int,
    admin: AreaAdmin,
    scope: AreaScopeDep,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> ApiKeyListOut:
    """List the area's API keys (screen 22). Never leaks the secret (TH-09)."""
    resolved = _resolve_area(area_id, scope)
    items, total = await service.list_api_keys(
        session, area_id=resolved, limit=min(limit, 100), offset=max(offset, 0)
    )
    return ApiKeyListOut(items=[_key_out(k) for k in items], total=total)


@router.delete("/{area_id}/api-keys/{key_pk}", response_model=ApiKeyOut)
async def revoke_api_key(
    area_id: int,
    key_pk: int,
    admin: AreaAdmin,
    scope: AreaScopeDep,
    session: SessionDep,
) -> ApiKeyOut:
    """Soft-revoke a key (effective < 1min — D-09). 404 cross-area (TH-03)."""
    resolved = _resolve_area(area_id, scope)
    api_key = await service.revoke_api_key(session, area_id=resolved, key_pk=key_pk)
    await session.commit()
    return _key_out(api_key)


# --- Webhook config ---------------------------------------------------------
def _endpoint_out(ep) -> WebhookEndpointOut:
    return WebhookEndpointOut(
        id=ep.id,
        url=ep.url,
        secret=ep.secret,
        events=ep.events,
        enabled=ep.enabled,
        created_at=ep.created_at.isoformat() if ep.created_at else None,
    )


@router.put("/{area_id}/webhook", response_model=WebhookEndpointOut)
async def configure_webhook(
    area_id: int,
    body: ConfigureWebhookBody,
    admin: AreaAdmin,
    scope: AreaScopeDep,
    session: SessionDep,
) -> WebhookEndpointOut:
    """Configure the area's outbound webhook (anti-SSRF validated — T-08 / TH-05)."""
    resolved = _resolve_area(area_id, scope)
    endpoint = await webhook_service.configure_endpoint(
        session,
        area_id=resolved,
        url=body.url,
        events=body.events,
        rotate_secret=body.rotate_secret,
        enabled=body.enabled,
    )
    await session.commit()
    return _endpoint_out(endpoint)


@router.get("/{area_id}/webhook", response_model=WebhookEndpointOut | None)
async def get_webhook(
    area_id: int,
    admin: AreaAdmin,
    scope: AreaScopeDep,
    session: SessionDep,
) -> WebhookEndpointOut | None:
    """Read the area's webhook config (None if not configured yet)."""
    resolved = _resolve_area(area_id, scope)
    endpoint = await webhook_repo.get_endpoint_for_area(session, area_id=resolved)
    return _endpoint_out(endpoint) if endpoint else None


@router.get("/{area_id}/webhook/deliveries", response_model=WebhookDeliveryListOut)
async def list_webhook_deliveries(
    area_id: int,
    admin: AreaAdmin,
    scope: AreaScopeDep,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> WebhookDeliveryListOut:
    """Paginated webhook-delivery history (status/attempts — screen 22)."""
    resolved = _resolve_area(area_id, scope)
    rows, total = await webhook_repo.list_deliveries_for_area(
        session, area_id=resolved, limit=min(limit, 100), offset=max(offset, 0)
    )
    items = [
        WebhookDeliveryOut(
            id=r.id,
            event_id=r.event_id,
            event_type=r.event_type,
            status=r.status,
            attempts=r.attempts,
            last_status_code=r.last_status_code,
            next_retry_at=r.next_retry_at.isoformat() if r.next_retry_at else None,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]
    return WebhookDeliveryListOut(items=items, total=total)


__all__ = ["router"]
