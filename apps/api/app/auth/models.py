"""User (global) + RefreshToken models.

`User` is a GLOBAL table (D-05): it does NOT inherit AreaScopedMixin. It carries
PII marked for LGPD (RN-021), lockout counters (5/15min, aware UTC — TD-010),
TOTP enrolment fields, and soft-delete/anonymisation columns as schema/flags
(effective jobs land in Phase 14).

`RefreshToken` stores only the SHA-256 hash of the opaque token, with rotation
(`rotated_at`) and a `family_id` so a detected reuse can revoke the whole family.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, TimestampMixin

# Platform-level role stored on the user (area roles live in area_admins).
PLATFORM_ADMIN_ROLE = "admin_plataforma"
DEFAULT_ROLE = "user"


class User(Base, TimestampMixin):
    """A global identity. Roles per area are resolved via memberships (D-09)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True, unique=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Platform role: 'admin_plataforma' or 'user' (area roles via area_admins).
    platform_role: Mapped[str] = mapped_column(String(32), nullable=False, default=DEFAULT_ROLE)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Lockout (5/15min, RN-011 / D-04) — datetimes aware UTC (TD-010) ---
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_failed_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)

    # --- TOTP (D-03): mandatory for platform admin; opt-in otherwise ---
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    totp_enrolled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Last accepted TOTP window — anti-replay within a window (TH-08).
    totp_last_window: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # --- LGPD lifecycle as schema/flags (effective jobs in Phase 14) ---
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    anonymized_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class RefreshToken(Base, TimestampMixin):
    """Opaque refresh token — only the SHA-256 hash is persisted (Pattern 4)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIG_ID, nullable=False, index=True)
    # Family id ties together a rotation chain so reuse revokes all siblings.
    family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
