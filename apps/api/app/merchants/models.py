"""Merchant + MerchantUser + MerchantSubscription models (F-01, D-05).

`Merchant` is AREA-SCOPED (AreaScopedMixin): every store belongs to exactly one
delivery area (Pádua in the pilot). It carries the state-machine `status`
(pending_payment / pending_validation / active / suspended), the geocoded point
(lat/lng nullable until resolved), and the BR identity (document normalised to
digits/uppercase + account_type). PII (document, phone) is masked in outputs and
NEVER logged (TH-06).

RN-011 uniqueness is per ACCOUNT TYPE: the composite UNIQUE
(`account_type`, `document`) lets a CPF and a CNPJ that happen to share a digit
string coexist, while blocking a true duplicate. `phone_e164` and `email` are
globally unique on the merchant (anti-duplicidade across the three identifiers).

`MerchantUser` links the owner `User` (argon2id via `auth/`) to the merchant.
`MerchantSubscription` ties a merchant to a `subscription_plan` with a status.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME, AreaScopedMixin, TimestampMixin

# Merchant state machine values (D-05). The valid transitions live in
# `state_machine.py`; these are the persisted strings.
MERCHANT_STATUSES = ("pending_payment", "pending_validation", "active", "suspended")
ACCOUNT_TYPES = ("cnpj", "cpf")


class Merchant(Base, AreaScopedMixin, TimestampMixin):
    """A store (F-01). Area-scoped; status is the state machine (D-05)."""

    __tablename__ = "merchants"
    __table_args__ = (
        # RN-011: uniqueness per account type (CPF vs CNPJ namespaces are separate).
        UniqueConstraint("account_type", "document", name="uq_merchants_account_type_document"),
        UniqueConstraint("phone_e164", name="uq_merchants_phone_e164"),
        UniqueConstraint("email", name="uq_merchants_email"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)

    account_type: Mapped[str] = mapped_column(String(8), nullable=False)
    # Normalised document (digits/uppercase). [PII] — masked in outputs, never logged.
    document: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    # [PII] E.164 phone — masked in outputs, never logged.
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)  # [PII]

    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_validation")

    # Geocoded point (resolved at signup; nullable until then).
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Receita validation bookkeeping (E4 / job retry).
    receita_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revalidation_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_revalidation_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)


class MerchantUser(Base, TimestampMixin):
    """Owner membership: links a global User to a Merchant with a role.

    GLOBAL (not AreaScopedMixin): the merchant already carries area_id; this is a
    pure association row mirroring `area_admins`.
    """

    __tablename__ = "merchant_users"
    __table_args__ = (
        UniqueConstraint("merchant_id", "user_id", name="uq_merchant_users_merchant_id_user_id"),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="owner")


# Recurring-billing state machine (Phase 10 / SAAS-BILLING §10). Separate from the
# legacy `status` (active/pending/canceled) which gates delivery creation today.
SUBSCRIPTION_BILLING_STATUSES = ("trial", "active", "blocked", "cancelado")


class MerchantSubscription(Base, AreaScopedMixin, TimestampMixin):
    """A merchant's subscription to a plan + recurring-billing state (Phase 10).

    The legacy `status` (active/pending/canceled) gates delivery creation (Phase 7).
    Phase 10 adds the recurring-billing columns: `billing_status` (trial/active/blocked/
    cancelado), the AES-encrypted card token, the aware-UTC `due_at`, the cycle/amount,
    the PIX-automatic state, and the scheduled-downgrade plan. Card/CVV are NEVER stored;
    only the Safe2Pay token, AES-256-GCM at rest (TH-B).
    """

    __tablename__ = "merchant_subscriptions"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("subscription_plans.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    # active (Free or paid confirmed) | pending (paid not yet confirmed) | canceled
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")

    # --- Recurring billing (Phase 10) ---
    billing_status: Mapped[str] = mapped_column(String(16), nullable=False, default="trial")
    payment_method: Mapped[str | None] = mapped_column(String(8), nullable=True)  # card | pix
    cycle: Mapped[str | None] = mapped_column(String(10), nullable=True)  # mensal | anual
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_at: Mapped[datetime | None] = mapped_column(UTC_DATETIME, nullable=True)
    # Safe2Pay card token, AES-256-GCM at rest (TH-B). NEVER the card number.
    safe2pay_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Scheduled downgrade (RN-029): the plan to switch to at cycle end; NULL otherwise.
    scheduled_plan_id: Mapped[int | None] = mapped_column(BIG_ID, nullable=True)

    # --- PIX Automático (Phase 10 / SAAS-BILLING §5.5) — pending until webhook APROVADA ---
    pix_autorizacao_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pix_autorizacao_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pix_qr_code: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    pix_qr_code_base64: Mapped[str | None] = mapped_column(Text, nullable=True)


class MerchantCourierFavorite(Base, AreaScopedMixin, TimestampMixin):
    """A store's favorite courier (RN-014 / D-06 — SEPARATE from blocks).

    Favorites enter the dispatch cascade FIRST, one at a time, ordered by
    `priority` (the store reorders ↑/↓ — D-01). Area-scoped pair (store↔courier);
    UNIQUE(area_id, merchant_id, courier_id) blocks a duplicate favorite. The
    composite index on (area_id, merchant_id) backs the candidate-build query so
    favorites load without a table scan (Gate 8 — no N+1). FK RESTRICT (DRV-002).
    """

    __tablename__ = "merchant_courier_favorites"
    __table_args__ = (
        UniqueConstraint(
            "area_id",
            "merchant_id",
            "courier_id",
            name="uq_merchant_courier_favorites_area_merchant_courier",
        ),
        # Candidate build: load a store's favorites by (area_id, merchant_id).
        Index(
            "ix_merchant_courier_favorites_area_id_merchant_id",
            "area_id",
            "merchant_id",
        ),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Cascade order within the favorites tier (D-01) — lower is offered first.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MerchantCourierBlock(Base, AreaScopedMixin, TimestampMixin):
    """A store's blocked courier (RN-014 / D-06 — SEPARATE from favorites).

    A blocked courier NEVER receives an offer from this store (neither favorites
    nor ranking). The block is PRIVATE to the store, valid only for THAT store,
    and does NOT affect the courier's score (RN-014). `reason` is the store's
    private note — never exposed to the courier. Area-scoped pair; UNIQUE per pair
    (a courier is blocked at most once). The (area_id, merchant_id) index backs the
    set-difference that removes blocked couriers before the cascade (TH-5).
    FK RESTRICT (DRV-002).
    """

    __tablename__ = "merchant_courier_blocks"
    __table_args__ = (
        UniqueConstraint(
            "area_id",
            "merchant_id",
            "courier_id",
            name="uq_merchant_courier_blocks_area_merchant_courier",
        ),
        # Candidate build: load a store's blocks by (area_id, merchant_id).
        Index(
            "ix_merchant_courier_blocks_area_id_merchant_id",
            "area_id",
            "merchant_id",
        ),
        Base.__table_args__,
    )

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("merchants.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    courier_id: Mapped[int] = mapped_column(
        BIG_ID,
        ForeignKey("couriers.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Private store-only note (RN-014) — NEVER exposed to the courier.
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
