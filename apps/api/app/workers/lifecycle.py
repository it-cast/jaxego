"""Lifecycle cron jobs (Phase 9 — D-06 / DEC-002 / D-07). All aware-UTC (TD-010).

- `finalize_deliveries`: ENTREGUE for >24h with NO open payment dispute → FINALIZADA
  (via `transition()` — append-only, D-06). Idempotent: only ENTREGUE rows move.
- `purge_locations`: HARD-delete `delivery_locations` of TERMINAL deliveries whose last
  sample is >24h old (retention/LGPD — TH-4 / Pitfall 3). Idempotent: re-running finds
  nothing new.
- `absent_timeout`: a delivery marked "ausente" (a refusal-reason marker) for >10min
  → flag it as eligible to "retornar" (D-07 E2). Idempotent (a flag, not a transition).
- `anonymize_inactive` (Phase 14 — D-01/D-02 / REQ-048 / LGPD): entities (couriers,
  recipients, users) untouched for >12 MONTHS → replace PII with a tombstone
  (name→placeholder, cpf/cpf_hash→tombstone, phone→null, email→tombstone), stamp
  `anonymized_at`, and append ONE `audit_log` row. IRREVERSIBLE. Statistical aggregates
  (counters, ids) are preserved. A record under LEGAL retention (financial/fiscal:
  platform_charges / escrow_ledger / direct_payment_confirmations) is NEVER anonymised.
  Idempotent: an already-anonymised row (`anonymized_at IS NOT NULL`) is skipped.
- `delete_ephemeral` (Phase 14 — D-01 / REQ-048 / LGPD): hard-delete non-consumed
  ephemeral data older than 30 DAYS — abandoned signups (inactive users never verified,
  no area membership, no financial trail) and expired refresh tokens. Idempotent.

Each job logs a processed COUNT + duration, never PII; a failure inside one row never
derails the sweep (best-effort per row). Registered in `WorkerSettings.cron_jobs`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.auth.models import RefreshToken, User
from app.couriers.models import Courier
from app.db.mixins import ensure_aware_utc
from app.deliveries.models import Delivery, Recipient
from app.deliveries.service import transition
from app.payments.models import EscrowLedger
from app.payments_direct.models import DirectPaymentConfirmation, PaymentDispute
from app.payments_direct.service import has_open_dispute
from app.tracking.models import DeliveryLocation

logger = structlog.get_logger("workers.lifecycle")

FINALIZE_AFTER = timedelta(hours=24)
PURGE_AFTER = timedelta(hours=24)
ABSENT_AFTER = timedelta(minutes=10)
# LGPD retention windows (D-01). 12 months ≈ 365 days; 30 days for ephemeral data.
ANONYMIZE_AFTER = timedelta(days=365)
EPHEMERAL_AFTER = timedelta(days=30)

# Irreversible PII tombstone — a fixed, non-reversible placeholder (D-02). The CPF
# (raw or hash) becomes a constant so it can never be reversed to the original.
_PII_NAME = "[anonimizado]"
_PII_TOMBSTONE = "anonymized"

_TERMINAL_STATES = ("FINALIZADA", "CANCELADA", "RECUSADA_NO_DESTINO")


async def finalize_deliveries(ctx: dict[str, Any]) -> int:
    """ENTREGUE >24h with no open dispute → FINALIZADA (D-06). Returns count."""
    started = datetime.now(UTC)
    cutoff = started - FINALIZE_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        rows = (
            (await session.execute(select(Delivery).where(Delivery.state == "ENTREGUE")))
            .scalars()
            .all()
        )
        for delivery in rows:
            delivered_at = delivery.delivered_at
            if delivered_at is None or ensure_aware_utc(delivered_at) > cutoff:
                continue
            if await has_open_dispute(session, delivery_id=delivery.id):
                continue  # an open dispute blocks finalisation (mediação Phase 11)
            await transition(
                session,
                delivery=delivery,
                to_state="FINALIZADA",
                actor_id=None,
                reason="auto_finalize_24h",
            )
            count += 1
        await session.commit()
    logger.info(
        "lifecycle.finalize_deliveries",
        finalized=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


async def purge_locations(ctx: dict[str, Any]) -> int:
    """Hard-delete delivery_locations of terminal deliveries >24h old (LGPD)."""
    started = datetime.now(UTC)
    cutoff = started - PURGE_AFTER
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        # Terminal deliveries only; samples older than the retention window.
        terminal_ids = (
            (await session.execute(select(Delivery.id).where(Delivery.state.in_(_TERMINAL_STATES))))
            .scalars()
            .all()
        )
        if not terminal_ids:
            logger.info("lifecycle.purge_locations", purged=0)
            return 0
        result = await session.execute(
            delete(DeliveryLocation).where(
                DeliveryLocation.delivery_id.in_(terminal_ids),
                DeliveryLocation.recorded_at < cutoff,
            )
        )
        await session.commit()
    count = result.rowcount or 0
    logger.info(
        "lifecycle.purge_locations",
        purged=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


async def absent_timeout(ctx: dict[str, Any]) -> int:
    """Mark deliveries 'ausente' >10min as eligible to return (D-07 E2).

    M1 marker: a delivery whose latest transition reason is 'absent' and whose
    `collected_at`/transition is >10min old. We set a flag in `notes` (idempotent
    string marker) since there is no dedicated column — the UI reads it to enable
    "Retornar ao estabelecimento". A full return automation is post-M1 (TD-007).
    """
    started = datetime.now(UTC)
    cutoff = started - ABSENT_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    marker = "[return_enabled]"
    async with session_factory() as session:
        rows = (
            (await session.execute(select(Delivery).where(Delivery.state == "COLETADA")))
            .scalars()
            .all()
        )
        for delivery in rows:
            # The "ausente" marker is carried in cancel_reason-like notes by the UI;
            # here we use `notes` containing 'absent' set when the courier reports it.
            if not delivery.notes or "absent" not in delivery.notes:
                continue
            collected = delivery.collected_at
            if collected is None or ensure_aware_utc(collected) > cutoff:
                continue
            if marker in delivery.notes:
                continue  # idempotent — already enabled
            delivery.notes = f"{delivery.notes} {marker}"
            count += 1
        await session.commit()
    logger.info(
        "lifecycle.absent_timeout",
        enabled=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


# ---------------------------------------------------------------------------
# Phase 14 — LGPD anonymisation (D-01/D-02 / REQ-048). IRREVERSIBLE + audited.
# ---------------------------------------------------------------------------
async def _courier_has_legal_retention(session: AsyncSession, *, courier_id: int) -> bool:
    """True if the courier is tied to a financial/fiscal record (legal retention).

    A courier that appears in `escrow_ledger`, `direct_payment_confirmations`, or
    `payment_disputes` is part of a transaction the platform MUST keep for
    fiscal/financial law — such a row is NEVER anonymised (D-02). (`platform_charges`
    has no direct `courier_id` — it is linked to the courier via the delivery/escrow.)
    """
    for model in (EscrowLedger, DirectPaymentConfirmation, PaymentDispute):
        exists = (
            await session.execute(
                select(func.count()).select_from(model).where(model.courier_id == courier_id)
            )
        ).scalar_one()
        if exists:
            return True
    return False


async def _user_has_legal_retention(session: AsyncSession, *, user_id: int) -> bool:
    """True if the user owns a courier profile under legal retention (D-02).

    A user is the global identity behind a courier; if that courier has a financial
    trail the user's PII is needed for the fiscal record → never anonymise.
    """
    courier_ids = (
        (await session.execute(select(Courier.id).where(Courier.user_id == user_id)))
        .scalars()
        .all()
    )
    for courier_id in courier_ids:
        if await _courier_has_legal_retention(session, courier_id=courier_id):
            return True
    return False


async def anonymize_inactive(ctx: dict[str, Any]) -> int:
    """Anonymise PII of entities inactive >12 months (D-01/D-02). Returns count.

    IRREVERSIBLE: name→placeholder, cpf/cpf_hash→tombstone, phone→null,
    email→tombstone; `anonymized_at` stamped; one `audit_log` row per entity. Skips
    rows already anonymised (idempotent) and rows under legal retention (D-02).
    "Inactive" = `updated_at` older than the window (the row has not changed in 12m).
    Best-effort per row: a failure on one entity never derails the sweep.
    """
    started = datetime.now(UTC)
    cutoff = started - ANONYMIZE_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        # --- Couriers ---
        couriers = (
            (
                await session.execute(
                    select(Courier).where(
                        Courier.updated_at < cutoff,
                        Courier.anonymized_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        for courier in couriers:
            try:
                if ensure_aware_utc(courier.updated_at) >= cutoff:
                    continue  # changed since the query (race) — skip
                if await _courier_has_legal_retention(session, courier_id=courier.id):
                    continue  # fiscal/financial retention (D-02)
                courier.full_name = _PII_NAME
                courier.phone_e164 = _PII_TOMBSTONE  # NOT NULL column → tombstone
                courier.email = _PII_TOMBSTONE
                courier.mei_cnpj = None
                courier.anonymized_at = started
                await write_audit(
                    session,
                    actor_id=None,
                    action="lgpd.anonymize.courier",
                    area_id=courier.area_id,
                    after={"entity": "courier", "id": courier.id},
                )
                count += 1
            except Exception:  # noqa: BLE001 — one bad row never derails the sweep
                logger.warning("lifecycle.anonymize_inactive.row_error", entity="courier")

        # --- Recipients ---
        recipients = (
            (
                await session.execute(
                    select(Recipient).where(
                        Recipient.updated_at < cutoff,
                        Recipient.anonymized_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        for recipient in recipients:
            try:
                if ensure_aware_utc(recipient.updated_at) >= cutoff:
                    continue
                recipient.name = _PII_NAME
                recipient.phone_e164 = _PII_TOMBSTONE  # NOT NULL column → tombstone
                recipient.email = None
                recipient.cpf_hash = _PII_TOMBSTONE
                recipient.anonymized_at = started
                await write_audit(
                    session,
                    actor_id=None,
                    action="lgpd.anonymize.recipient",
                    area_id=recipient.area_id,
                    after={"entity": "recipient", "id": recipient.id},
                )
                count += 1
            except Exception:  # noqa: BLE001
                logger.warning("lifecycle.anonymize_inactive.row_error", entity="recipient")

        # --- Users (global) ---
        users = (
            (
                await session.execute(
                    select(User).where(
                        User.updated_at < cutoff,
                        User.anonymized_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        for user in users:
            try:
                if ensure_aware_utc(user.updated_at) >= cutoff:
                    continue
                if await _user_has_legal_retention(session, user_id=user.id):
                    continue  # owns a courier with a financial trail (D-02)
                # email is UNIQUE NOT NULL → tombstone made unique by id.
                user.email = f"{_PII_TOMBSTONE}+{user.id}@anonymized.invalid"
                user.name = _PII_NAME
                user.phone = None
                user.cpf = None
                user.is_active = False
                user.anonymized_at = started
                await write_audit(
                    session,
                    actor_id=None,
                    action="lgpd.anonymize.user",
                    area_id=None,
                    after={"entity": "user", "id": user.id},
                )
                count += 1
            except Exception:  # noqa: BLE001
                logger.warning("lifecycle.anonymize_inactive.row_error", entity="user")

        await session.commit()
    logger.info(
        "lifecycle.anonymize_inactive",
        anonymized=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


# ---------------------------------------------------------------------------
# Phase 14 — LGPD ephemeral hard-delete (D-01 / REQ-048).
# ---------------------------------------------------------------------------
async def delete_ephemeral(ctx: dict[str, Any]) -> int:
    """Hard-delete non-consumed ephemeral data older than 30 days (D-01). Returns count.

    Two classes of ephemeral row:
      - abandoned signups: a `User` never activated (`is_active=False`,
        `anonymized_at IS NULL`), with NO area membership, NO courier profile and NO
        financial trail, untouched for >30 days. (An anonymised user is left alone.)
      - expired refresh tokens: `RefreshToken.expires_at` in the past beyond the
        window (a vencida idempotency key is already swept by `purge_idempotency_keys`).
    Idempotent: a re-run on an already-clean window is a 0-row no-op.
    """
    from app.areas.models import AreaAdmin
    from app.merchants.models import MerchantUser

    started = datetime.now(UTC)
    cutoff = started - EPHEMERAL_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        # --- Expired refresh tokens (consumed/expired credentials). ---
        result = await session.execute(delete(RefreshToken).where(RefreshToken.expires_at < cutoff))
        count += result.rowcount or 0

        # --- Abandoned signups: inactive, never anonymised, no attachments. ---
        candidates = (
            (
                await session.execute(
                    select(User).where(
                        User.is_active.is_(False),
                        User.anonymized_at.is_(None),
                        User.updated_at < cutoff,
                        User.platform_role != "admin_plataforma",
                    )
                )
            )
            .scalars()
            .all()
        )
        for user in candidates:
            try:
                has_area = (
                    await session.execute(
                        select(func.count())
                        .select_from(AreaAdmin)
                        .where(AreaAdmin.user_id == user.id)
                    )
                ).scalar_one()
                has_merchant = (
                    await session.execute(
                        select(func.count())
                        .select_from(MerchantUser)
                        .where(MerchantUser.user_id == user.id)
                    )
                ).scalar_one()
                has_courier = (
                    await session.execute(
                        select(func.count()).select_from(Courier).where(Courier.user_id == user.id)
                    )
                ).scalar_one()
                if has_area or has_merchant or has_courier:
                    continue  # attached → not an abandoned signup
                if await _user_has_legal_retention(session, user_id=user.id):
                    continue  # defensive — financial trail
                await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
                await session.delete(user)
                count += 1
            except Exception:  # noqa: BLE001 — one bad row never derails the sweep
                logger.warning("lifecycle.delete_ephemeral.row_error", entity="user")

        await session.commit()
    logger.info(
        "lifecycle.delete_ephemeral",
        deleted=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count
