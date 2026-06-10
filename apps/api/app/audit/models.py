"""AuditLog model — GLOBAL, append-only (RN-012 / D-10/D-11).

This table is INSERT-only, guaranteed at the database by triggers (created in the
migration, T-12) that SIGNAL on UPDATE/DELETE. It does NOT inherit
AreaScopedMixin: it is global (D-05), but keeps a nullable `area_id` so an action
can be attributed to an area when one applies.

`cross_area_bypass` records when a platform admin acted outside their scope — the
bypass is NEVER silent (RN-001).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UTC_DATETIME


class AuditLog(Base):
    """Append-only audit trail: actor, action, before/after, IP, timestamp."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # Nullable: global table, but attribute to an area when one applies.
    area_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6-safe
    cross_area_bypass: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # No TimestampMixin: append-only means no updated_at; one created_at only.
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
