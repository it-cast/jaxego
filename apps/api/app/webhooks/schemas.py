"""Webhook admin contracts (Pydantic v2, extra='forbid' — A03)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.webhooks.models import WEBHOOK_EVENTS


class ConfigureWebhookBody(BaseModel):
    """Configure/update the area's webhook endpoint (screen 22)."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=8, max_length=2048)
    events: list[str] = Field(default_factory=list)
    enabled: bool = True
    rotate_secret: bool = False


class WebhookEndpointOut(BaseModel):
    """The configured endpoint. The secret is shown so the area can configure the
    receiver (it is the area's OWN signing secret, not a credential into Jaxegô)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    secret: str
    events: str
    enabled: bool
    created_at: str | None = None


class WebhookDeliveryOut(BaseModel):
    """A webhook-delivery history row (screen 22). No payload PII surfaced here."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    event_type: str
    status: str
    attempts: int
    last_status_code: int | None
    next_retry_at: str | None
    created_at: str | None = None


class WebhookDeliveryListOut(BaseModel):
    """Paginated webhook-delivery history."""

    items: list[WebhookDeliveryOut]
    total: int


SUPPORTED_EVENTS = list(WEBHOOK_EVENTS)
