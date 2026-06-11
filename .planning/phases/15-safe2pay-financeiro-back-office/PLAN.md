# Phase 15: Safe2Pay financeiro (back-office) — fatura, disputas, saques - PLAN

**Milestone:** MS-06 (PÓS-DEPLOY) · **has_ui:** true · **has_payments:** true · **integration_check:** true (Safe2Pay)
**Status:** Ready for execution · **Migration:** 0013 · **Date:** 2026-06-11 (autopilot)
**Depende de:** [14] ✓ · **Última phase do projeto.**

## Goal
Ligar o dinheiro do back-office direto: fatura mensal com bloqueio por vencimento (REQ-037, F-03 E5),
resolução financeira de disputas com bloqueio 90d (REQ-039, RN-027 — fatia deferida da Phase 13),
saques do entregador (REQ-038, R$ 20), e conciliação diária (REQ-040). Tudo atrás do `PaymentPort` com
**Stub** (DEC-003); produção gated pelo contrato (TD-10-01..04, RELEASE-CHECKLIST).

## Skills Consultadas
- `domain/saas-billing-canonical` (**LEI — CLAUDE.md §18**) — fatura/competência/vencimento/bloqueio
  seguem `docs/SAAS-BILLING-DOCS.md`; money em centavos, idempotência por Reference (D-01/D-02).
- `domain/safe2pay-escrow-br` (**LEI**) — saque/repasse/estorno/escrow: novo método `payout` no
  PaymentPort, restituição em falha, confirmação antes de mover dinheiro (D-04, TH-07).
- `owasp-security` (idempotência, webhooks, auth) — threat model TH-01..TH-08: IDOR no saque, FOR UPDATE
  no saldo, bloqueio auditado, webhook com dedup/GET-confirm. Gate 4 baseline em RESEARCH.md.
- `quality/observability-production` — conciliação diária + alertas de divergência (D-05); sem PII em log.
- `ux-advanced/payment-checkout-ux` — pagar fatura (tela 15), recibo (tela 08).
- `ux-advanced/trust-safety-ux` — transparência de valores, saque e disputa.
- `ux-advanced/data-tables-ux` — fatura/extrato/histórico de saques (telas 15/16).
- `product/component-library-governance` — reusa jx-data-table/estados/confirmação; novos jx-money/jx-invoice-summary.
- `quality/accessibility-pro` — status cor+texto, confirmação de saque foco-preso, aria-live no erro de mínimo.
- `ux-advanced/design-tokens-system` + `ui-ux-pro-max` — UI-SPEC via tokens; zero hex.
- `ux-advanced/dark-mode-theming` (DEC-001) — telas nos 2 temas.
- `ux-advanced/empty-states-polish` — empties de fatura/extrato/saques.
- `br/ux-copywriting-ptbr` — copy de fatura/saque/vencimento (UI-SPEC §copy).
- `domain/mysql-schema-design` — migration 0013 (invoices/line_items/withdrawals/dispute_blocks); reversível; FK RESTRICT.
- `domain/fastapi-production-patterns` — módulos invoices/withdrawals, jobs arq.

## Skills Dispensadas (com justificativa)
- `mobile/push-notifications-architecture` — notificação de fatura/saque reusa o multicanal da Phase 9
  (não há arquitetura nova de push aqui).
- `domain/github-actions-ci`/`monorepo-deploy-safety` — deploy/CI foi a Phase 14; aqui é feature financeira.

## Threat model (herdado — RESEARCH §Security Baseline)
TH-01 IDOR saque (escopo+404) · TH-02 corrida (FOR UPDATE + Reference UNIQUE) · TH-03 fatura derivada
(não-input) · TH-04 webhook repasse (HMAC+dedup+GET — Phase 10) · TH-05 bloqueio disputa auditado ·
TH-06 PII/financeiro fora de log · TH-07 nunca mover dinheiro sem confirmação · TH-08 bloqueio de fatura
server-side. **secure-phase + integration_check validam.**

## Tech debt deste plano (Regra 11)
- **TD-10-01..04** (cutover Safe2Pay) — esta phase é onde o financeiro direto fica completo; o cutover de
  produção continua dependente do contrato. O novo método `payout` herda essa dependência (LOW-2 → TD).
- **TD-13-01** (revenue share %) — **agora ganha efeito financeiro** na fatura; confirmar % com o dono
  antes do go-live (promover para pre_launch_blocker se a fatura de produção depender dele).

## LOW confidence → tasks (Regra 12)
- **LOW-1 (RESEARCH §2):** "2 procedentes/30d → bloqueio 90d" → **Task T-05** com clock controlado.
- **LOW-2 (RESEARCH §3):** método `payout` do PaymentPort (shape Safe2Pay `[ASSUMIDO]`) → **Task T-06**
  + **TD-15-01** (cutover do repasse, pre_launch — depende do contrato).

## Tasks (waves)

### Wave 1 — Schema + fatura + bloqueio (backend)
- **T-01** Migration 0013: `platform_invoices`, `invoice_line_items`, `withdrawals`,
  `dispute_blocks` (area-scoped, centavos, FK RESTRICT, índices, reversível + teste @mysql).
- **T-02** Módulo `invoices/`: job dia 1º fecha fatura (idempotente, 1/loja/competência) somando taxas
  registradas; status em aberto/vencida/paga; pagar fatura via PaymentPort.
- **T-03** Guard F-03 E5: fatura vencida >7d → bloqueia criação no MESMO ponto de `deliveries.service:313`.

### Wave 2 — Disputa financeira + saques + conciliação (backend)
- **T-04** Decisão financeira da disputa (estende `PaymentDispute`): procedente → ajuste via
  PaymentPort; registro auditado.
- **T-05** Regra RN-027: 2 procedentes/30d → `dispute_blocks` 90d (modalidade direta bloqueada, guard na
  criação) + job de expiração. Clock controlado (LOW-1).
- **T-06** Módulo `withdrawals/`: saque do saldo escrow (FOR UPDATE), **mín. R$ 20** (seed), repasse via
  **novo `PaymentPort.payout`** (Stub + adapter `[ASSUMIDO]`), **falha → restitui** (compensação idempotente).
- **T-07** Conciliação diária estendendo `payments/reconcile.py` (divergência → alerta). Job arq.

### Wave 3 — Frontend (telas 15/16/08)
- **T-08** `jx-money` + `jx-invoice-summary` (+ stories + a11y).
- **T-09** Tela 15 (fatura loja: resumo + linhas + pagar + banner de vencimento), 16 (extrato/saldo +
  saque mín. R$ 20, mobile), 08 (recibo do direto). Rotas lazy. Zero hex.
- **T-10** Serviços Angular + signals; estados empty/loading/error; testes.

### Wave 4 — Integration check (Gate 5)
- **T-11** `gsd-integration-checker`: round-trip financeiro com Stub — fatura fecha e bloqueia >7d;
  saque < R$20 rejeitado; saque falha → saldo restituído; 2 disputas procedentes/30d → bloqueio 90d;
  conciliação detecta divergência sintética.

## Verificação (ROADMAP)
- Job fecha fatura dia 1º; vencida >7 dias → criação de entrega bloqueada (F-03 E5).
- "Não recebi" → ENTREGUE + disputa; 2 procedentes/30d → modalidade direta bloqueada 90 dias.
- Saque falha → saldo restituído; saque < R$ 20 → rejeitado.
- Wireframe-contract de 08, 15, 16.
- `uv run pytest` (not-mysql) + `pytest -m mysql` migration 0013 + `ng test`/build/lint verdes.
- Gate 8: idempotência financeira, sem mover dinheiro sem confirmação, FOR UPDATE no saldo, sem PII em log.

## Parallel-hint
`module-split` — invoices ∥ withdrawals ∥ reconcile são disjuntos. Wave 1 (schema) antes; Waves 2/3 paralelizáveis.
