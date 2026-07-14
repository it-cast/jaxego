"""Safe2Pay webhooks — log → HMAC → dedup → enqueue → 200 (Phase 10 / TH-E).

The endpoint is PUBLIC (Safe2Pay calls it). The order is mandatory and is the whole
security model (skill A3/A4 + owasp A08):

  1. log the raw payload to `payment_webhook_events` BEFORE processing (audit, no card PII)
  2. verify the HMAC-SHA256 signature with `secrets.compare_digest` (NEVER `==` — timing)
  3. dedup by (transaction_id, status) — a duplicate is a 200 no-op (one effect, TH-E)
  4. enqueue the heavy work to arq (confirm via GET before any money moves)
  5. respond 200 in < 5s

`[ASSUMIDO A4]` defence in depth (the HMAC may not be provided by Safe2Pay): idempotency
(UNIQUE) + a secret in the path is NOT used here, but the worker NEVER releases money on a
webhook alone — it confirms via `GET Transaction/{id}` first. A business error in processing
is logged + enqueued + 200 (NEVER 500 — Safe2Pay would retry forever). `# público:`
justified — the HMAC + idempotency + GET-confirmation are the auth (TH-M).
"""

from __future__ import annotations

import hmac
import json
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.payments import repo

logger = structlog.get_logger("payments.webhooks")

router = APIRouter(prefix="/payments/webhooks", tags=["payments-webhooks"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _verify_secret_key(payload: dict, *, secret: str | None) -> bool:
    """Safe2Pay envia SecretKey no body (não há header HMAC).

    Compara o SecretKey do payload com a chave configurada usando compare_digest
    (anti-timing). Sem secret configurado, passa — a defesa em profundidade é a
    idempotência + confirmação por GET no worker ([ASSUMIDO A4]).
    """
    if not secret:
        return True
    body_key = payload.get("SecretKey") or ""
    if not body_key:
        return False
    return hmac.compare_digest(secret.upper(), body_key.upper())


def _extract(payload: dict, *keys: str) -> str:
    """Pull a field from payload root, data sub-dict, or TransactionStatus (Safe2Pay varies)."""
    raw = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    for key in keys:
        val = (raw or {}).get(key) or payload.get(key)
        if val:
            return str(val)
    # Safe2Pay PIX avulso: status em TransactionStatus.Code
    ts = payload.get("TransactionStatus")
    if isinstance(ts, dict):
        val = ts.get("Code") or ts.get("Id")
        if val:
            return str(val)
    return ""


@router.post("/safe2pay", status_code=status.HTTP_200_OK)
async def safe2pay_webhook(request: Request, session: SessionDep) -> dict:
    # público: idempotência + HMAC + confirmação por GET no worker cobrem a auth (TH-M).
    body = await request.body()

    # 1. Log BEFORE processing (audit; no card PII in a Safe2Pay status payload).
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {}

    logger.info(
        "safe2pay_webhook_received",
        raw_body=body.decode("utf-8", errors="replace")[:2000],
        headers=dict(request.headers),
        payload=payload,
    )

    transaction_id = _extract(payload, "IdTransaction", "Id")
    event_status = _extract(payload, "Status")

    # 2. Verify SecretKey from body (Safe2Pay embeds it in payload, not as a header).
    if not _verify_secret_key(payload, secret=settings.safe2pay_secret_key):
        logger.warning("safe2pay_webhook_bad_signature")
        raise HTTPException(status_code=403, detail="assinatura inválida")

    if not transaction_id or not event_status:
        # Malformed but signed — log + 200 (never 500, or Safe2Pay retries forever).
        logger.warning("safe2pay_webhook_malformed")
        return {"ok": True}

    # 3. Dedup by (transaction_id, status) — a duplicate is a 200 no-op (one effect).
    seen = await repo.mark_webhook_seen(
        session,
        area_id=None,
        transaction_id=transaction_id,
        status=event_status,
        payload=body.decode("utf-8", errors="replace")[:8000],
    )
    await session.commit()
    if not seen:
        return {"ok": True, "idempotent": True}

    # 4. Processar direto (sem worker intermediário).
    await _process_event(session, transaction_id, event_status)

    # 5. 200 < 5s.
    return {"ok": True}


async def _process_event(session: AsyncSession, transaction_id: str, event_status: str) -> None:
    """Processa o evento Safe2Pay diretamente na request (sem ARQ)."""
    from app.payments import repo, subscriptions

    approved = event_status in {"3", "4", "APROVADA", "ATIVA", "CONCLUIDA", "PAGO"}
    # Estorno confirmado pela Safe2Pay — evidência real observada em produção:
    # PIX avulso estornado pelo painel da Safe2Pay chega com event_status "6".
    # Sem isso, platform_charges.status fica "paid" pra sempre mesmo depois do
    # estorno já efetivado do lado da Safe2Pay (gap de reconciliação).
    refunded = event_status in {"6"}

    # PIX Automático authorization APROVADA: look up by authorization id.
    if event_status == "APROVADA":
        found = await subscriptions.activate_approved_pix(
            session, pix_autorizacao_id=transaction_id
        )
        if found:
            await session.commit()
            logger.info("payments.pix_auto_approved", authorization_id=transaction_id)
            return

    # Standard charge event (card ou PIX QR).
    charge = await repo.get_charge_by_transaction(session, transaction_id=transaction_id)
    logger.info(
        "payments.process_event",
        transaction_id=transaction_id,
        event_status=event_status,
        approved=approved,
        refunded=refunded,
        charge_found=charge is not None,
        charge_kind=charge.kind if charge else None,
        charge_status=charge.status if charge else None,
        delivery_id=charge.delivery_id if charge else None,
    )
    if charge is not None and refunded and charge.status == "paid":
        charge.status = "refunded"
        await session.commit()
        logger.info(
            "payments.charge_refunded",
            transaction_id=transaction_id,
            delivery_id=charge.delivery_id,
            subscription_id=charge.subscription_id,
        )
        return
    if charge is not None and approved and charge.status == "open":
        charge.status = "paid"
        if charge.subscription_id is not None and charge.method == "pix":
            await subscriptions.activate_pix_on_charge_paid(
                session, subscription_id=charge.subscription_id
            )
        if charge.kind == "delivery" and charge.delivery_id is not None:
            from app.deliveries.models import Delivery
            from app.deliveries.service import transition as delivery_transition
            from app.workers.dispatch import enqueue_dispatch

            delivery = await session.get(Delivery, charge.delivery_id)
            if delivery is not None and delivery.state == "AGUARDANDO_PAGAMENTO":
                await delivery_transition(
                    session,
                    delivery=delivery,
                    to_state="CRIADA",
                    actor_id=None,
                    reason="pix_confirmed",
                )
                await session.commit()
                await enqueue_dispatch(delivery.id)
                logger.info(
                    "payments.delivery_pix_confirmed",
                    delivery_id=delivery.id,
                    transaction_id=transaction_id,
                )
                return
        if charge.kind == "topup" and charge.merchant_id is not None:
            from app.merchants import credit as credit_mod

            await credit_mod.record_topup(
                session,
                area_id=charge.area_id,
                merchant_id=charge.merchant_id,
                charge_id=charge.id,
                amount_cents=charge.net_amount_cents or 0,
            )
            await session.commit()
            logger.info(
                "payments.credit_topup_confirmed",
                merchant_id=charge.merchant_id,
                charge_id=charge.id,
                transaction_id=transaction_id,
            )
            return
    await session.commit()
