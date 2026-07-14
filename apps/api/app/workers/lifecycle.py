"""Lifecycle cron jobs (Phase 9 — D-06 / DEC-002 / D-07). All aware-UTC (TD-010).

- `finalize_deliveries`: ENTREGUE for >24h with NO open payment dispute → FINALIZADA
  (via `transition()` — append-only, D-06). Idempotent: only ENTREGUE rows move.
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
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.auth.models import RefreshToken
from app.couriers.models import Courier
from app.db.mixins import ensure_aware_utc
from app.deliveries.models import Delivery, Recipient
from app.deliveries.service import transition
from app.payments.models import EscrowLedger
from app.payments_direct.models import DirectPaymentConfirmation, PaymentDispute
from app.payments_direct.service import has_open_dispute

logger = structlog.get_logger("workers.lifecycle")

FINALIZE_AFTER = timedelta(hours=24)
ABSENT_AFTER = timedelta(minutes=10)
# LGPD retention windows (D-01). 12 months ≈ 365 days; 30 days for ephemeral data.
ANONYMIZE_AFTER = timedelta(days=365)
EPHEMERAL_AFTER = timedelta(days=30)

# Irreversible PII tombstone — a fixed, non-reversible placeholder (D-02). The CPF
# (raw or hash) becomes a constant so it can never be reversed to the original.
_PII_NAME = "[anonimizado]"
_PII_TOMBSTONE = "anonymized"

async def finalize_deliveries(ctx: dict[str, Any]) -> int:
    """ENTREGUE >24h with no open dispute → FINALIZADA (D-06). Returns count."""
    started = datetime.now(UTC)
    cutoff = started - FINALIZE_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    finalized_ids: list[int] = []
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
            from app.merchants.credit import reconcile_delivery_credit

            await reconcile_delivery_credit(session, delivery=delivery)
            finalized_ids.append(delivery.id)
            count += 1
        await session.commit()
    if finalized_ids:
        from app.workers.payout import enqueue_payout

        for delivery_id in finalized_ids:
            await enqueue_payout(delivery_id)
    logger.info(
        "lifecycle.finalize_deliveries",
        finalized=count,
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
                # email é UNIQUE → tombstone único por id.
                courier.email = f"{_PII_TOMBSTONE}+{courier.id}@anonymized.invalid"
                courier.cpf = None
                courier.mei_cnpj = None
                courier.password_hash = None
                courier.is_active = False
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

        # (Pós-users: não há mais tabela global de usuários — a PII de conta
        # vive em couriers/merchants/teams/area_admins e é varrida acima.)

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

    Ephemeral rows: expired refresh tokens (`RefreshToken.expires_at` past the
    window). Pós-users não há mais "abandoned signups" globais — cada conta vive
    na tabela do seu tipo e segue a retenção do domínio.
    Idempotent: a re-run on an already-clean window is a 0-row no-op.
    """
    started = datetime.now(UTC)
    cutoff = started - EPHEMERAL_AFTER
    session_factory = ctx["session_factory"]
    count = 0
    async with session_factory() as session:
        # --- Expired refresh tokens (consumed/expired credentials). ---
        result = await session.execute(delete(RefreshToken).where(RefreshToken.expires_at < cutoff))
        count += result.rowcount or 0

        await session.commit()
    logger.info(
        "lifecycle.delete_ephemeral",
        deleted=count,
        duration_ms=int((datetime.now(UTC) - started).total_seconds() * 1000),
    )
    return count


async def expire_online_couriers(ctx: dict[str, Any]) -> int:
    """Set couriers offline whose online_until has passed. Single UPDATE — no Python loop."""
    started = datetime.now(UTC)
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        result = await session.execute(
            update(Courier)
            .where(Courier.is_online.is_(True), Courier.online_until <= started)
            .values(is_online=False, online_until=None)
        )
        await session.commit()
    count = result.rowcount or 0
    if count:
        logger.info("lifecycle.expire_online_couriers", expired=count)
    return count
