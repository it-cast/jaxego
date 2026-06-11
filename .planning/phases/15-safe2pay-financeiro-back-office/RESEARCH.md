# Phase 15: Safe2Pay financeiro (back-office) - Research

**Status:** Ready for planning · **Date:** 2026-06-11 (autopilot) · **[PÓS-DEPLOY]**

## Billing canônico (LEI — CLAUDE.md §18)
Antes de codar, seguir `docs/SAAS-BILLING-DOCS.md` + skill `domain/saas-billing-canonical` +
`domain/safe2pay-escrow-br`. Não inventar lógica de billing. Padrões obrigatórios: money em centavos
inteiros, idempotência por `Reference`, escrow atrás de `PaymentPort`, valores parametrizados.

## Achados técnicos

### 1. Fatura mensal (REQ-037, RN-025)
- A entrega direta **já registra** a taxa efetiva (Phase 10: "the effective charge is the Phase 11
  invoice"). Job dia 1º agrega por (loja, competência) → `platform_invoices` + `invoice_line_items`.
- Vencimento parametrizado; **>7 dias vencida → bloqueia criação** no MESMO guard de
  `deliveries.service:313` (subscription) — apenas adiciona a condição (F-03 E5).
- **Confidence: HIGH** (gancho já existe).

### 2. Disputa — consequência financeira (REQ-039, RN-027)
- Estende `PaymentDispute`: decisão procedente/improcedente (UI de triagem = Phase 13). **2 procedentes
  em 30d → bloqueia modalidade direta 90d** (auditado; job expira o bloqueio). Procedente → ajuste via
  `PaymentPort.refund`/crédito. **Confidence: MED** (regra temporal precisa de teste com clock).

### 3. Saques (REQ-038, R$ 20)
- Saldo de escrow liberado (`escrow.py`/ledger). `withdrawals` (area-scoped). **< R$ 20 → rejeitado**
  (seed). Repasse via **novo método do PaymentPort** (`payout`/`transfer_to_subaccount`) — endpoint
  Safe2Pay `[ASSUMIDO]` (TD), Stub no dev/test. **Falha → restitui saldo** (compensação idempotente).
- **Confidence: MED** — adiciona método ao Port; shape real do repasse Safe2Pay é TD (contrato).

### 4. Conciliação diária (REQ-040)
- Estende `payments/reconcile.py`: cruza escrow/charges/repasses/estornos × extrato PSP (Stub);
  divergência → registro + alerta. Idempotente. **Confidence: HIGH** (extensão).

### 5. UI telas 08/15/16
- 15 fatura da loja, 16 extrato/saldo + saque do entregador, 08 recibo do direto. Reusa jx-data-table.
- **Confidence: HIGH**.

## Security Baseline (Gate 4 — owasp-security + safe2pay-escrow-br)

| # | Ameaça | Mitigação |
|---|---|---|
| TH-01 | Saque fraudulento / IDOR (A01) | saque escopado ao próprio courier (area_id+courier_id → 404); valor ≤ saldo liberado; idempotência por Reference |
| TH-02 | Double-spend / corrida no saque | `SELECT ... FOR UPDATE` no saldo (padrão do aceite Phase 8); 1 saque por Reference (UNIQUE) |
| TH-03 | Fatura adulterada / valor errado | linhas derivadas de entregas registradas (não input do usuário); money em centavos; soma auditável |
| TH-04 | Webhook de repasse/estorno forjado | reusa o pipeline da Phase 10 (HMAC + dedup IdTransaction + confirma via GET antes de mover dinheiro) |
| TH-05 | Bloqueio de disputa burlado | bloqueio 90d auditado (append-only); guard na criação direta; job de expiração idempotente |
| TH-06 | PII/dados financeiros em log (A09) | sem CPF/cartão/telefone em log; valores ok, identificadores tokenizados |
| TH-07 | Estorno/repasse sem confirmação | nunca move dinheiro só por evento; confirma via PaymentPort/GET (DEC-003 defesa em profundidade) |
| TH-08 | Bloqueio de fatura contornável | guard no MESMO ponto de criação (server-side), não só UI |

## LOW confidence → tasks (Regra 12)
- **LOW-1:** "2 procedentes/30d → 90d" → **Task** com teste de clock controlado (janela 30d, expiração 90d).
- **LOW-2:** método de repasse do PaymentPort (shape Safe2Pay `[ASSUMIDO]`) → **Task** + **TD** (cutover contrato).

## Skills aplicáveis
- `domain/saas-billing-canonical` (LEI) · `domain/safe2pay-escrow-br` (LEI) · `owasp-security`
  (idempotência/webhooks/auth) · `quality/observability-production` (conciliação, alertas) ·
  `ux-advanced/payment-checkout-ux` · `ux-advanced/trust-safety-ux` (disputas/saques) ·
  `ux-advanced/data-tables-ux` (faturas/extrato) · matriz UI + `br/ux-copywriting-ptbr` · `domain/mysql-schema-design`
