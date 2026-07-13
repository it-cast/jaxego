"""Declarative mixins shared by domain models (mysql-schema-design).

`TimestampMixin` adds UTC `created_at`/`updated_at` as `DATETIME(6)` (TD-010:
the database column stores microsecond UTC; aware UTC is enforced at the app
boundary). `AreaScopedMixin` adds the multi-area isolation column
(`area_id BIGINT NOT NULL` + index + FK RESTRICT) that EVERY domain table must
carry (ADR-001 / D-05). Global tables (`users`, `audit_log`, `ai_usage_log`)
deliberately do NOT inherit `AreaScopedMixin`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import DATETIME as MYSQL_DATETIME
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

# DATETIME(6) on MySQL (microsecond precision); plain DateTime elsewhere (SQLite).
UTC_DATETIME = DateTime(timezone=True).with_variant(MYSQL_DATETIME(fsp=6), "mysql")

# BIGINT on MySQL; INTEGER on SQLite (SQLite only auto-increments INTEGER PK).
BIG_ID = BigInteger().with_variant(Integer, "sqlite")


def _utcnow() -> datetime:
    """Aware UTC now (TD-010: never naive)."""
    return datetime.now(UTC)


def ensure_aware_utc(value: datetime) -> datetime:
    """Coerce a DB-read datetime to aware UTC (TD-010 read boundary).

    Some drivers (SQLite/aiosqlite, and MySQL DATETIME) return naive datetimes
    even for `DateTime(timezone=True)` columns. We store UTC, so a naive value
    read back IS UTC — attach the tzinfo so comparisons never mix naive/aware.
    """
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class CredentialsMixin:
    """Login credentials + lockout counters for actor tables (pós-users).

    Cada tipo de acesso (courier, merchant, team, area_admin, platform_admin)
    guarda as próprias credenciais na própria tabela. `password_hash` é nullable
    para linhas legadas sem login (ex.: team sem responsável); o login falha
    com mensagem genérica quando NULL.
    """

    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Lockout 5/15min (RN-011 / D-04) — datetimes aware UTC (TD-010).
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_failed_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class TimestampMixin:
    """UTC created/updated timestamps as DATETIME(6)."""

    created_at: Mapped[datetime] = mapped_column(
        UTC_DATETIME,
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTC_DATETIME,
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )


class AreaScopedMixin:
    """Multi-area isolation column for every DOMAIN table (ADR-001 / D-05).

    Adds `area_id BIGINT NOT NULL`, an index, and a FK RESTRICT to `areas`.
    The isolation invariant is enforced structurally in three layers; this is
    layer 1 (schema). Layer 2 is `AreaScopedRepository` (WHERE area_id); layer 3
    is the `area_scope` FastAPI dependency.
    """

    @declared_attr
    def area_id(cls) -> Mapped[int]:  # noqa: N805 (SQLAlchemy declared_attr API)
        return mapped_column(
            BIG_ID,
            ForeignKey("areas.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=False,
            index=True,
        )
