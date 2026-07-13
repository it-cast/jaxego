"""Area + AreaAdmin models (multi-area core).

`Area` is the tenant boundary (REQ-002): a unique `codename`, JSON `config` for
local rules, and `deleted_at` for soft-archive (never hard-deleted when it has
dependents — DRV-002). `AreaAdmin` é a conta do admin da cidade (CredentialsMixin):
email/senha vivem aqui — não há mais tabela global `users`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, CredentialsMixin, TimestampMixin


class Area(Base, TimestampMixin):
    """A delivery area — the tenant boundary; every domain row carries area_id."""

    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    codename: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # Local, configurable business rules (REQ-002) — JSON keeps it flexible.
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Soft-archive (DRV-002): not deletable with dependents -> archive instead.
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class Zona(Base, AreaScopedMixin, TimestampMixin):
    """Sub-division of an Area with a GeoJSON polygon boundary.

    Zones replace per-area polygon: the admin_area draws zones instead of a
    single area boundary. Each team will set a minimum price per zone (future).
    """

    __tablename__ = "zonas"
    __table_args__ = Base.__table_args__

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    boundary: Mapped[dict | None] = mapped_column(JSON, nullable=True)


# AreaAdmin role values (subset of the 6-role taxonomy relevant to this phase).
AREA_ADMIN_ROLES = ("owner", "manager", "viewer")


class AreaAdmin(Base, AreaScopedMixin, CredentialsMixin, TimestampMixin):
    """Conta do admin da cidade — email/senha próprios + role (D-08/D-09)."""

    __tablename__ = "area_admins"
    __table_args__ = (
        UniqueConstraint("email", name="uq_area_admins_email"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="viewer")
