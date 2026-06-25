"""Area + AreaAdmin models (multi-area core).

`Area` is the tenant boundary (REQ-002): a unique `codename`, JSON `config` for
local rules, and `deleted_at` for soft-archive (never hard-deleted when it has
dependents — DRV-002). `AreaAdmin` links a global `User` to an `Area` with a
role (owner/manager/viewer) and is itself area-scoped (inherits AreaScopedMixin).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin


class Area(Base, TimestampMixin):
    """A delivery area — the tenant boundary; every domain row carries area_id."""

    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    codename: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # Local, configurable business rules (REQ-002) — JSON keeps it flexible.
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # GeoJSON polygon boundary for the area (drawn on a map by the admin).
    boundary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Soft-archive (DRV-002): not deletable with dependents -> archive instead.
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


# AreaAdmin role values (subset of the 6-role taxonomy relevant to this phase).
AREA_ADMIN_ROLES = ("owner", "manager", "viewer")


class AreaAdmin(Base, AreaScopedMixin, TimestampMixin):
    """Membership linking a User to an Area with an admin role (D-08/D-09)."""

    __tablename__ = "area_admins"
    __table_args__ = (
        UniqueConstraint("area_id", "user_id", name="uq_area_admins_area_id_user_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="viewer")
