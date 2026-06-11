"""Recurring subscription billing (Phase 10 — SAAS-BILLING §5-10, REQ-010/011).

The mechanics are the canonical SAAS-BILLING mechanics, ported NestJS→FastAPI and made
aware-UTC (TD-010 — Pitfall 4). Money is integer cents (DRV-009).

- `activate_card`: tokenise (production) / charge raw (sandbox handled by the adapter),
  store the AES-encrypted token, set `active`, record the initial paid charge + the next
  open charge.
- `activate_pix`: create the PIX autorização; the subscription stays PENDING until the
  webhook APROVADA activates it (SAAS-BILLING §6.2).
- `charge_due_subscriptions` (cron): charge open card subscriptions due today; idempotent
  (each charge advances `due_at` so a re-run in the same day finds nothing — TH-J).
- `sync_delinquency` (cron): >10d → blocked, >20d → cancelado (aware-UTC).
- `assert_subscription_active`: the guard that blocks delivery creation when blocked/cancelado.
- `prorata_upgrade_cents` / `change_plan`: upgrade pro-rata now (cents), downgrade scheduled
  for cycle end (RN-029).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import AppError, NotFoundError
from app.db.mixins import ensure_aware_utc
from app.merchants.models import MerchantSubscription
from app.payments import repo
from app.payments.crypto import encrypt_token
from app.payments.port import Customer, PaymentPort
from app.plans.models import SubscriptionPlan

logger = structlog.get_logger("payments.subscriptions")

# SAAS-BILLING §10 — grace windows (seed/config if ever parametrised).
GRACE_BLOCK_DAYS = 10
GRACE_CANCEL_DAYS = 20
# [ASSUMIDO A8] annual = monthly × 10 (2 months free) — policy via seed, adjust freely.
ANNUAL_MULTIPLIER = 10


class SubscriptionBlockedError(AppError):
    """The store's subscription is blocked/cancelled — delivery creation is blocked."""

    status_code = 402
    code = "subscription_blocked"

    def __init__(self, billing_status: str) -> None:
        self.billing_status = billing_status
        if billing_status == "cancelado":
            msg = "Sua assinatura foi cancelada. Reative um plano para voltar a criar entregas."
        else:
            msg = "Sua assinatura está bloqueada por falta de pagamento. Regularize para continuar."
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Delinquency (SAAS-BILLING §10) — aware-UTC (TD-010).
# ---------------------------------------------------------------------------
def classify_delinquency(days: int) -> str:
    """>20d → cancelado, >10d → blocked, else active (SAAS-BILLING §10)."""
    if days > GRACE_CANCEL_DAYS:
        return "cancelado"
    if days > GRACE_BLOCK_DAYS:
        return "blocked"
    return "active"


def days_overdue(due_at: datetime | None, now: datetime) -> int:
    """Whole days overdue based on the oldest open charge (aware-UTC, TD-010)."""
    if due_at is None:
        return 0
    due = ensure_aware_utc(due_at)
    return max(0, (now.date() - due.date()).days)


def _next_due(base: datetime, cycle: str | None) -> datetime:
    """Next due date for a cycle (mensal +1 month ≈ 30d; anual +365d). aware-UTC."""
    days = 365 if cycle == "anual" else 30
    return base + timedelta(days=days)


def _plan_amount_cents(plan: SubscriptionPlan, cycle: str | None) -> int:
    """The recurring amount for a plan+cycle (annual = monthly × 10 — A8)."""
    if cycle == "anual":
        return plan.price_cents * ANNUAL_MULTIPLIER
    return plan.price_cents


# ---------------------------------------------------------------------------
# Activation — card (tokenised) / PIX automático.
# ---------------------------------------------------------------------------
async def activate_card(
    session: AsyncSession,
    *,
    subscription_id: int,
    plan_id: int,
    cycle: str,
    raw_card_token: str,
    customer_name: str,
    customer_document: str,
    customer_email: str,
    payment: PaymentPort,
) -> MerchantSubscription:
    """Activate a card subscription: charge, store the AES token, set active."""
    sub = await session.get(MerchantSubscription, subscription_id)
    if sub is None:
        raise NotFoundError("Assinatura não encontrada.")
    plan = await session.get(SubscriptionPlan, plan_id)
    if plan is None:
        raise NotFoundError("Plano não encontrado.")
    amount = _plan_amount_cents(plan, cycle)
    customer = Customer(name=customer_name, document=customer_document, email=customer_email)

    now = datetime.now(UTC)
    reference = f"sub_{sub.id}_{int(now.timestamp())}"
    result = await payment.charge_with_token(
        token=raw_card_token, amount_cents=amount, reference=reference, customer=customer
    )

    sub.plan_id = plan.id
    sub.billing_status = "active"
    sub.payment_method = "card"
    sub.cycle = cycle
    sub.amount_cents = amount
    sub.safe2pay_token = encrypt_token(result.token or raw_card_token)
    next_due = _next_due(now, cycle)
    sub.due_at = next_due

    # Initial paid charge + next open charge.
    await repo.record_charge(
        session,
        area_id=sub.area_id,
        idempotency_key=reference,
        transaction_id=result.transaction_id,
        amount_cents=amount,
        method="card",
        kind="subscription",
        status="paid",
        subscription_id=sub.id,
        due_at=now,
    )
    await repo.record_charge(
        session,
        area_id=sub.area_id,
        idempotency_key=f"sub_{sub.id}_next_{int(next_due.timestamp())}",
        transaction_id=None,
        amount_cents=amount,
        method="card",
        kind="subscription",
        status="open",
        subscription_id=sub.id,
        due_at=next_due,
    )
    await session.flush()
    logger.info("subscription.activated_card", subscription_id=sub.id, amount_cents=amount)
    return sub


async def activate_pix(
    session: AsyncSession,
    *,
    subscription_id: int,
    plan_id: int,
    cycle: str,
    customer_name: str,
    customer_document: str,
    customer_email: str,
    payment: PaymentPort,
) -> MerchantSubscription:
    """Create the PIX autorização; subscription stays PENDING until webhook APROVADA."""
    sub = await session.get(MerchantSubscription, subscription_id)
    if sub is None:
        raise NotFoundError("Assinatura não encontrada.")
    plan = await session.get(SubscriptionPlan, plan_id)
    if plan is None:
        raise NotFoundError("Plano não encontrado.")
    amount = _plan_amount_cents(plan, cycle)
    customer = Customer(name=customer_name, document=customer_document, email=customer_email)

    now = datetime.now(UTC)
    reference = f"sub_{sub.id}_pix_{int(now.timestamp())}"
    result = await payment.create_pix_authorization(
        amount_cents=amount, customer=customer, reference=reference
    )

    # Do NOT activate yet — store the pending PIX state (SAAS-BILLING §6.2).
    sub.payment_method = "pix"
    sub.cycle = cycle
    sub.amount_cents = amount
    sub.pix_autorizacao_id = result.authorization_id
    sub.pix_autorizacao_status = "CRIADA"
    sub.pix_qr_code = result.qr_code
    sub.pix_qr_code_base64 = result.qr_code_base64

    await repo.record_charge(
        session,
        area_id=sub.area_id,
        idempotency_key=reference,
        transaction_id=result.transaction_id,
        amount_cents=amount,
        method="pix",
        kind="subscription",
        status="open",
        subscription_id=sub.id,
        due_at=now,
    )
    await session.flush()
    logger.info("subscription.pix_pending", subscription_id=sub.id)
    return sub


# ---------------------------------------------------------------------------
# Cron: charge due card subscriptions (idempotent — TH-J).
# ---------------------------------------------------------------------------
async def charge_due_subscriptions(
    session_factory: async_sessionmaker[AsyncSession], payment: PaymentPort
) -> int:
    """Charge active card subscriptions whose due_at has passed. Returns count."""
    now = datetime.now(UTC)
    charged = 0
    async with session_factory() as session:
        stmt = select(MerchantSubscription).where(
            MerchantSubscription.billing_status == "active",
            MerchantSubscription.payment_method == "card",
            MerchantSubscription.due_at.is_not(None),
        )
        subs = (await session.execute(stmt)).scalars().all()
        for sub in subs:
            if sub.due_at is None or ensure_aware_utc(sub.due_at) > now:
                continue
            if not sub.safe2pay_token:
                continue
            from app.payments.crypto import decrypt_token

            token = decrypt_token(sub.safe2pay_token)
            reference = f"sub_{sub.id}_{int(ensure_aware_utc(sub.due_at).timestamp())}"
            customer = Customer(name="Assinante", document="", email="")
            try:
                result = await payment.charge_with_token(
                    token=token,
                    amount_cents=sub.amount_cents,
                    reference=reference,
                    customer=customer,
                )
            except Exception:  # noqa: BLE001 — a failed charge is logged; delinquency cron handles it
                logger.warning("subscription.charge_failed", subscription_id=sub.id)
                continue
            await repo.record_charge(
                session,
                area_id=sub.area_id,
                idempotency_key=reference,
                transaction_id=result.transaction_id,
                amount_cents=sub.amount_cents,
                method="card",
                kind="subscription",
                status="paid",
                subscription_id=sub.id,
                due_at=ensure_aware_utc(sub.due_at),
            )
            sub.due_at = _next_due(ensure_aware_utc(sub.due_at), sub.cycle)
            charged += 1
        await session.commit()
    logger.info("subscription.charge_due", charged=charged)
    return charged


# ---------------------------------------------------------------------------
# Cron: delinquency sync (10/20d, aware-UTC).
# ---------------------------------------------------------------------------
async def sync_delinquency(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Transition active/blocked subscriptions by overdue days. Returns count changed."""
    now = datetime.now(UTC)
    changed = 0
    async with session_factory() as session:
        from app.payments.models import PlatformCharge

        stmt = select(MerchantSubscription).where(
            MerchantSubscription.billing_status.in_(("active", "blocked"))
        )
        subs = (await session.execute(stmt)).scalars().all()
        for sub in subs:
            oldest = (
                (
                    await session.execute(
                        select(PlatformCharge)
                        .where(
                            PlatformCharge.subscription_id == sub.id,
                            PlatformCharge.status == "open",
                        )
                        .order_by(PlatformCharge.due_at.asc())
                    )
                )
                .scalars()
                .first()
            )
            due = oldest.due_at if oldest else None
            status = classify_delinquency(days_overdue(due, now))
            if status != "active" and sub.billing_status != status:
                sub.billing_status = status
                changed += 1
            elif status == "active" and sub.billing_status == "blocked":
                sub.billing_status = "active"
                changed += 1
        await session.commit()
    logger.info("subscription.delinquency_sync", changed=changed)
    return changed


# ---------------------------------------------------------------------------
# Guard — block delivery creation when blocked/cancelado (SAAS-BILLING §9).
# ---------------------------------------------------------------------------
async def assert_subscription_active(
    session: AsyncSession, *, merchant_id: int, area_id: int
) -> None:
    """Raise SubscriptionBlockedError if the merchant's subscription is blocked/cancelado."""
    stmt = select(MerchantSubscription).where(
        MerchantSubscription.merchant_id == merchant_id,
        MerchantSubscription.area_id == area_id,
    )
    sub = (await session.execute(stmt)).scalars().first()
    if sub is None:
        return  # no subscription row → let the plan-limit path handle it
    if sub.billing_status in ("blocked", "cancelado"):
        raise SubscriptionBlockedError(sub.billing_status)


# ---------------------------------------------------------------------------
# Plan change — upgrade pro-rata now / downgrade scheduled (RN-029).
# ---------------------------------------------------------------------------
def prorata_upgrade_cents(
    *,
    current_cents: int,
    target_cents: int,
    now: datetime,
    cycle_end: datetime,
    cycle_days: int,
) -> int:
    """Pro-rata charge for an upgrade: (target-current) × remaining_days/cycle_days.

    Integer cents; never negative (a downgrade returns 0 — it is scheduled, not charged).
    """
    diff = target_cents - current_cents
    if diff <= 0:
        return 0
    remaining = max(0, (ensure_aware_utc(cycle_end).date() - ensure_aware_utc(now).date()).days)
    return (diff * remaining) // cycle_days


async def change_plan(
    session: AsyncSession,
    *,
    subscription_id: int,
    target_plan_id: int,
    payment: PaymentPort,
) -> dict[str, Any]:
    """Upgrade (charge pro-rata now, switch immediately) or downgrade (schedule)."""
    sub = await session.get(MerchantSubscription, subscription_id)
    if sub is None:
        raise NotFoundError("Assinatura não encontrada.")
    target = await session.get(SubscriptionPlan, target_plan_id)
    if target is None:
        raise NotFoundError("Plano não encontrado.")
    target_amount = _plan_amount_cents(target, sub.cycle)

    now = datetime.now(UTC)
    cycle_end = ensure_aware_utc(sub.due_at) if sub.due_at else _next_due(now, sub.cycle)
    cycle_days = 365 if sub.cycle == "anual" else 30

    if target_amount > sub.amount_cents:
        # Upgrade — charge pro-rata now and switch immediately.
        prorata = prorata_upgrade_cents(
            current_cents=sub.amount_cents,
            target_cents=target_amount,
            now=now,
            cycle_end=cycle_end,
            cycle_days=cycle_days,
        )
        charged = 0
        if prorata > 0 and sub.payment_method == "card" and sub.safe2pay_token:
            from app.payments.crypto import decrypt_token

            token = decrypt_token(sub.safe2pay_token)
            reference = f"sub_{sub.id}_upgrade_{int(now.timestamp())}"
            result = await payment.charge_with_token(
                token=token,
                amount_cents=prorata,
                reference=reference,
                customer=Customer(name="Assinante", document="", email=""),
            )
            await repo.record_charge(
                session,
                area_id=sub.area_id,
                idempotency_key=reference,
                transaction_id=result.transaction_id,
                amount_cents=prorata,
                method="card",
                kind="subscription",
                status="paid",
                subscription_id=sub.id,
                due_at=now,
            )
            charged = prorata
        sub.plan_id = target.id
        sub.amount_cents = target_amount
        sub.scheduled_plan_id = None
        await session.flush()
        return {"kind": "upgrade", "charged_cents": charged, "effective": "now"}

    if target_amount < sub.amount_cents:
        # Downgrade — schedule for cycle end; no charge now.
        sub.scheduled_plan_id = target.id
        await session.flush()
        return {"kind": "downgrade", "charged_cents": 0, "effective": "cycle_end"}

    return {"kind": "noop", "charged_cents": 0, "effective": "now"}
