# Phase 15 — Reconciliação (prometido vs. real)

**Data:** 2026-06-12 (autopilot) · **Status:** sem gaps; produção gated pelo contrato (TD-10-0x/15-01)

| Prometido (PLAN) | Real | Evidência |
|---|---|---|
| Migration 0013 reversível (4 tabelas + decisão de disputa) | ✓ | `alembic/versions/0013_financeiro_back_office.py` + teste @mysql |
| Fatura mensal (job dia 1º, 1/loja/competência, status) | ✓ | `app/invoices/` (deriva taxa registrada na entrega) |
| Bloqueio F-03 E5 (vencida >7d → criação bloqueada) | ✓ | `app/deliveries/service.py` (mesmo guard do subscription, server-side) |
| Disputa: decisão financeira (procedente → ajuste via PaymentPort) | ✓ | `app/payments_direct/disputes.py` (auditado) |
| RN-027: 2 procedentes/30d → bloqueio direto 90d + expiração | ✓ | `dispute_blocks` + job (clock controlado nos testes) |
| Saques: saldo escrow (FOR UPDATE), mín. R$20, payout, falha→restitui | ✓ | `app/withdrawals/` + `PaymentPort.payout` (Stub+adapter) |
| Conciliação diária (divergência → alerta) | ✓ | `app/payments/reconcile.py` estendido + job |
| Telas 15/16/08 + jx-money + jx-invoice-summary | ✓ | `apps/web/src/features/...` + `shared/components/{money,invoice-summary}/` |
| Zero hex / testes verdes / lint | ✓ | backend 494 + frontend 204; ruff + ng lint limpos; zero hex |

## Desvios / TD
- **TD-15-01** (pre_launch_high): cutover do repasse `payout` Safe2Pay (shape `[ASSUMIDO]`, depende do contrato).
- Frontend adicionou endpoints read-only thin (`/invoices/{id}/lines`, `/withdrawals/extract`,
  `/withdrawals/history`, `/deliveries/{id}/receipt`) reusando repos existentes — documentado no EXECUTION-LOG.
- Entrega direta passou a registrar `delivery.fee_cents` (sem isso a fatura não teria base) — Rule 2.

## Gaps abertos
Nenhum de código. **Produção** do financeiro direto continua gated pelo contrato Safe2Pay
(TD-10-01..04 + TD-15-01), como previsto na DEC-004 e no RELEASE-CHECKLIST. Pendente `pytest -m mysql`
(migration 0013) em DB live.
