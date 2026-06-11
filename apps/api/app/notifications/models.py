"""Notification + PushSubscription models (RN-018 / RN-031 — multicanal).

`Notification` is the durable record of EVERY channel attempt (push/sms/email) for a
delivery moment (accepted / on_the_way / delivered), with the channel + status +
moment — so the dispatcher's fallback decisions are auditable (no PII in the row:
only ids + channel + status). `PushSubscription` registers a device's Web Push
subscription (endpoint + keys JSON) so the push channel has a target. Both area-scoped.

aware-UTC `created_at` (TD-010). No PII (phone/email) is stored in `Notification` —
only WHICH channel was tried and its status (A09 / TH-8).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

NOTIFICATION_MOMENTS = ("accepted", "on_the_way", "delivered")
NOTIFICATION_CHANNELS = ("push", "sms", "email")
NOTIFICATION_STATUSES = ("sent", "failed", "skipped")


class Notification(Base, AreaScopedMixin):
    """One channel attempt for a delivery moment (auditable, no PII — A09)."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_delivery_id", "delivery_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    moment: Mapped[str] = mapped_column(String(16), nullable=False)
    channel: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)


class PushSubscription(Base, AreaScopedMixin, TimestampMixin):
    """A device Web Push subscription (endpoint + keys). Target for the push channel."""

    __tablename__ = "push_subscriptions"
    __table_args__ = (
        UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
        Index("ix_push_subscriptions_user_id", "user_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    # The subscriber (a recipient may be anonymous; user_id NULL for public devices).
    user_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    delivery_id: Mapped[int | None] = mapped_column(
        BIG_ID,
        ForeignKey("deliveries.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    endpoint: Mapped[str] = mapped_column(String(512), nullable=False)
    # The browser subscription JSON (endpoint + p256dh + auth). Not PII.
    keys_json: Mapped[str] = mapped_column(Text, nullable=False)
