"""PlatformAdmin + RefreshToken models (pós-remoção da tabela global `users`).

Cada tipo de acesso guarda as próprias credenciais na própria tabela
(CredentialsMixin): couriers, merchants, teams, area_admins e platform_admins.
`PlatformAdmin` é a única conta com TOTP (obrigatório — D-03).

`RefreshToken` stores only the SHA-256 hash of the opaque token, with rotation
(`rotated_at`) and a `family_id` so a detected reuse can revoke the whole family.
`actor_type` + `actor_id` identificam a conta dona da sessão.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, CredentialsMixin, TimestampMixin

# Tipos de ator — cada um autentica na sua tabela e no seu endpoint de login.
ACTOR_COURIER = "courier"
ACTOR_MERCHANT = "merchant"
ACTOR_TEAM = "team"
ACTOR_AREA_ADMIN = "area_admin"
ACTOR_PLATFORM_ADMIN = "platform_admin"
ACTOR_TYPES = (
    ACTOR_COURIER,
    ACTOR_MERCHANT,
    ACTOR_TEAM,
    ACTOR_AREA_ADMIN,
    ACTOR_PLATFORM_ADMIN,
)


class PlatformAdmin(Base, CredentialsMixin, TimestampMixin):
    """Admin do sistema (antes: users.platform_role='admin_plataforma')."""

    __tablename__ = "platform_admins"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    # --- TOTP (D-03): mandatory for platform admin ---
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    totp_enrolled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Last accepted TOTP window — anti-replay within a window (TH-08).
    totp_last_window: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # --- LGPD lifecycle as schema/flags ---
    deleted_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class RefreshToken(Base, TimestampMixin):
    """Opaque refresh token — only the SHA-256 hash is persisted (Pattern 4)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    # Conta dona da sessão: tipo + id na tabela do tipo.
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[int] = mapped_column(BIG_ID, nullable=False, index=True)
    # Family id ties together a rotation chain so reuse revokes all siblings.
    family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
