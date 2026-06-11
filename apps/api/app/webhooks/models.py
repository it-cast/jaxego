"""Webhook endpoint + delivery models (Phase 12 — D-06/D-07).

`WebhookEndpoint` is AREA-SCOPED: one endpoint per area (the configured URL +
HMAC secret + subscribed events). The `secret` is shown to the area admin to
configure the receiver and is used to SIGN outbound payloads — it is the area's
own secret (not a credential into Jaxegô), stored for signing. The URL passed the
anti-SSRF guard at registration (T-08).

`WebhookDelivery` is one delivery attempt-set per event (TH-10): it carries the
ULID `event_id` (anti-replay handle for the receiver), the event type, the JSON
payload, the attempt counter, the next-retry instant, the last response status,
and a terminal `status` (pending/delivered/failed). The arq job (T-09) drives the
EXACT backoff `[0,30,120,600,3600,14400,43200,86400]s`; after the 8th failure →
`failed` + alerta.

All datetimes are aware UTC (TD-010). FK RESTRICT throughout.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

# The 6 delivery events surfaced to integrators (D-08), mapped from the 7-state
# machine of Phase 7. RECUSADA_NO_DESTINO is folded into `delivery.canceled`.
WEBHOOK_EVENTS = (
    "delivery.created",
    "delivery.accepted",
    "delivery.collected",
    "delivery.delivered",
    "delivery.finalized",
    "delivery.canceled",
)

# Terminal delivery status of a webhook attempt-set (TH-10).
WEBHOOK_DELIVERY_STATUSES = ("pending", "delivered", "failed")


class WebhookEndpoint(Base, AreaScopedMixin, TimestampMixin):
    """The area's configured outbound webhook (URL + signing secret + events)."""

    __tablename__ = "webhook_endpoints"
    __table_args__ = (
        # One endpoint per area (D-06). The area_id index from the mixin covers lookups.
        UniqueConstraint("area_id", name="uq_webhook_endpoints_area_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    # The receiver URL — https only, anti-SSRF validated at registration (T-08 / A10).
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    # HMAC signing secret (the area's own secret, rotatable). Not a credential INTO us.
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    # Space-separated subscribed events (subset of WEBHOOK_EVENTS); empty = all.
    events: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)


class WebhookDelivery(Base, AreaScopedMixin, TimestampMixin):
    """One outbound webhook attempt-set for a single event (TH-10 / D-07)."""

    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        # The ULID event id is unique (anti-replay handle for the receiver, D-06).
        UniqueConstraint("event_id", name="uq_webhook_deliveries_event_id"),
        # The job sweeps pending deliveries due for the next attempt.
        Index("ix_webhook_deliveries_status_next_retry_at", "status", "next_retry_at"),
        Index("ix_webhook_deliveries_endpoint_id", "endpoint_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    endpoint_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("webhook_endpoints.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # ULID — the `X-Jaxego-Event-Id` (anti-replay handle for the receiver, 5-min window).
    event_id: Mapped[str] = mapped_column(String(26), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # The minimised JSON payload (RN-013 — no recipient phone, no pre-pickup address).
    payload: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    last_status_code: Mapped[int | None] = mapped_column(nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
