"""API key + idempotency models (Phase 12 — RN-020 / D-01 / D-04).

`ApiKey` is AREA-SCOPED: a key authenticates an integrator (Menu Certo first) to
ONE area. The plaintext secret is NEVER stored — only its argon2id hash
(`secret_hash`) plus the public, indexed `key_id` (the lookup handle, not a
credential). The full secret (`jxg_<key_id>_<secret>`) is returned ONCE at
creation and never again (D-01). `revoked_at` is a soft-revoke (auditoria, never
DELETE); a revoked key fails auth (< 1min propagation, cache invalidated on
revoke — D-09).

`ApiIdempotencyKey` is the 24h response snapshot (D-04 / TH-04): keyed by
`(api_key_id, idempotency_key)`, it stores the SHA-256 of the canonical request
body and the cached response (status + JSON) so a replay returns the SAME
response and a same-key/different-body request returns 409. `expires_at` is swept
by the purge job (T-05).

All datetimes are aware UTC (TD-010). FK RESTRICT on every relation (transacional).
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


class ApiKey(Base, AreaScopedMixin, TimestampMixin):
    """An area-scoped integrator API key (RN-020). Secret stored as argon2id hash."""

    __tablename__ = "api_keys"
    __table_args__ = (
        # Lookup handle: the request carries `key_id`, we fetch the row by it (public,
        # non-secret — the secret is verified against `secret_hash`). UNIQUE so a key_id
        # resolves to exactly one row.
        UniqueConstraint("key_id", name="uq_api_keys_key_id"),
        # List the area's keys (screen 22) without a scan.
        Index("ix_api_keys_area_id_created_at", "area_id", "created_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    # Public, indexed lookup handle (the prefix part of `jxg_<key_id>_<secret>`).
    key_id: Mapped[str] = mapped_column(String(32), nullable=False)
    # argon2id hash of the secret — NEVER the plaintext (TH-01 / A07).
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Human label shown in the admin list (screen 22). No PII.
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Space-separated scopes (e.g. "deliveries:write"). Narrow by default.
    scopes: Mapped[str] = mapped_column(String(255), nullable=False, default="deliveries:write")

    # Soft-revoke (auditoria) — a non-null value fails auth (D-09). Never DELETE.
    revoked_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)

    @property
    def is_active(self) -> bool:
        """True when the key has not been revoked."""
        return self.revoked_at is None


class ApiIdempotencyKey(Base, AreaScopedMixin, TimestampMixin):
    """24h idempotency snapshot for the public create endpoint (D-04 / TH-04)."""

    __tablename__ = "api_idempotency_keys"
    __table_args__ = (
        # The dedup handle: one snapshot per (key, idempotency_key). A replay locks
        # this row FOR UPDATE and returns the stored response.
        UniqueConstraint(
            "api_key_id", "idempotency_key", name="uq_api_idempotency_keys_apikey_key"
        ),
        # Purge job (T-05) sweeps by expiry.
        Index("ix_api_idempotency_keys_expires_at", "expires_at"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    api_key_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("api_keys.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    # SHA-256 (hex) of the canonical request body — distinguishes replay from reuse (409).
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # Cached response (status + JSON body) so the replay is byte-identical (D-04).
    response_status: Mapped[int] = mapped_column(nullable=False)
    response_body: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False)
