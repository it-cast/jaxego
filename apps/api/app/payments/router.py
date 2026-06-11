"""/v1/payments — RSA public key, subscription activation, plan change, history.

Auth (TH-M): the store endpoints resolve `merchant_scope` (A01 — IDOR closed by
(area_id, merchant_id) in the WHERE clause). `GET /chave-publica` is PUBLIC and justified
(it only exposes the RSA PUBLIC key so the client can encrypt the card — no secret). The
card never arrives in plaintext: the client sends an opaque RSA-OAEP `card_blob`, the
backend decrypts it in memory (NEVER logged/persisted — A09) and forwards only the token.
"""

from __future__ import annotations

import json
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.db.session import get_session
from app.deliveries.dependencies import MerchantScopeDep
from app.merchants.models import MerchantSubscription
from app.payments import crypto, subscriptions
from app.payments.factory import get_payment_adapter
from app.payments.models import PlatformCharge
from app.payments.schemas import (
    ChargeHistoryItem,
    PlanChangeBody,
    PlanChangeOut,
    PublicKeyOut,
    SubscribeBody,
    SubscriptionOut,
)

logger = structlog.get_logger("payments.router")

router = APIRouter(prefix="/payments", tags=["payments"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/chave-publica", response_model=PublicKeyOut)
async def public_key() -> PublicKeyOut:
    # público: expõe APENAS a chave RSA pública (sem segredo) para o cliente cifrar o cartão.
    return PublicKeyOut(public_key=crypto.public_key_pem())


def _subscription_out(sub: MerchantSubscription) -> SubscriptionOut:
    return SubscriptionOut(
        subscription_id=sub.id,
        billing_status=sub.billing_status,
        payment_method=sub.payment_method,
        plan_id=sub.plan_id,
        amount_cents=sub.amount_cents,
        next_due_at=sub.due_at.isoformat() if sub.due_at else None,
        qr_code=sub.pix_qr_code,
        qr_code_base64=sub.pix_qr_code_base64,
    )


async def _resolve_subscription(
    session: AsyncSession, *, merchant_id: int, area_id: int
) -> MerchantSubscription:
    stmt = select(MerchantSubscription).where(
        MerchantSubscription.merchant_id == merchant_id,
        MerchantSubscription.area_id == area_id,
    )
    sub = (await session.execute(stmt)).scalars().first()
    if sub is None:
        raise ValidationAppError("Assinatura não encontrada para esta loja.")
    return sub


@router.post("/assinar", response_model=SubscriptionOut)
async def subscribe(
    body: SubscribeBody, scope: MerchantScopeDep, session: SessionDep
) -> SubscriptionOut:
    """Activate a plan by card (RSA blob → token) or PIX automático."""
    sub = await _resolve_subscription(session, merchant_id=scope.merchant_id, area_id=scope.area_id)
    payment = get_payment_adapter()

    if body.method == "card":
        if not body.card_blob:
            raise ValidationAppError("Dados do cartão ausentes.")
        # Decrypt in memory ONLY — the card JSON is NEVER logged/persisted (A09).
        card_json = crypto.rsa_decrypt_card(body.card_blob)
        card = json.loads(card_json)
        # The adapter tokenises (prod) / charges raw (sandbox); we pass the raw token
        # placeholder — the Stub/adapter abstracts the sandbox difference (Pitfall 5).
        from app.payments.port import CardData

        tokenised = await payment.tokenize_card(
            CardData(
                holder=card["nomeTitular"],
                number=card["numeroCartao"],
                expiration=card["validade"],
                cvv=card["cvv"],
            )
        )
        result = await subscriptions.activate_card(
            session,
            subscription_id=sub.id,
            plan_id=body.plan_id,
            cycle=body.cycle,
            raw_card_token=tokenised or "raw_sandbox",
            customer_name=card.get("nomeTitular", ""),
            customer_document=body.customer_document,
            customer_email=str(body.customer_email),
            payment=payment,
        )
    else:
        from app.merchants.models import Merchant

        merchant = await session.get(Merchant, scope.merchant_id)
        result = await subscriptions.activate_pix(
            session,
            subscription_id=sub.id,
            plan_id=body.plan_id,
            cycle=body.cycle,
            customer_name=merchant.trade_name if merchant else "Loja",
            customer_document=body.customer_document,
            customer_email=str(body.customer_email),
            payment=payment,
        )
    await session.commit()
    return _subscription_out(result)


@router.get("/assinatura", response_model=SubscriptionOut)
async def get_subscription(scope: MerchantScopeDep, session: SessionDep) -> SubscriptionOut:
    sub = await _resolve_subscription(session, merchant_id=scope.merchant_id, area_id=scope.area_id)
    return _subscription_out(sub)


@router.post("/assinatura/mudar-plano", response_model=PlanChangeOut)
async def change_plan(
    body: PlanChangeBody, scope: MerchantScopeDep, session: SessionDep
) -> PlanChangeOut:
    """Upgrade (pro-rata now) or downgrade (scheduled) — RN-029 (anti-dark-pattern UI)."""
    sub = await _resolve_subscription(session, merchant_id=scope.merchant_id, area_id=scope.area_id)
    result = await subscriptions.change_plan(
        session,
        subscription_id=sub.id,
        target_plan_id=body.target_plan_id,
        payment=get_payment_adapter(),
    )
    await session.commit()
    return PlanChangeOut(
        kind=result["kind"],
        charged_cents=result["charged_cents"],
        effective=result["effective"],
    )


@router.get("/cobrancas", response_model=list[ChargeHistoryItem])
async def charge_history(scope: MerchantScopeDep, session: SessionDep) -> list[ChargeHistoryItem]:
    """The store's charge history (area-scoped, single query — no N+1)."""
    stmt = (
        select(PlatformCharge)
        .where(PlatformCharge.area_id == scope.area_id)
        .order_by(PlatformCharge.created_at.desc())
        .limit(100)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        ChargeHistoryItem(
            id=c.id,
            kind=c.kind,
            amount_cents=c.amount_cents,
            method=c.method,
            status=c.status,
            transaction_id=c.transaction_id,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in rows
    ]
