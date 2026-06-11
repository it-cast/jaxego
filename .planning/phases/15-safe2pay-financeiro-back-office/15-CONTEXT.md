# Phase 15: Safe2Pay financeiro (back-office) — fatura, disputas, saques - Context

**Gathered:** 2026-06-11 (modo --auto, autopilot)
**Status:** Ready for planning
**[PÓS-DEPLOY · MS-06]** — ex-Phase 11, a ÚLTIMA do projeto (DEC-004). Código nasce verde com Stub;
ativação de produção atrás do contrato Safe2Pay (TD-10-01..04).

<domain>
## Phase Boundary

Back-office financeiro do pagamento direto e da plataforma, sobre a infra da Phase 10 (escrow,
`PaymentPort`, subconta) e o primitivo `payment_dispute` da Phase 9: (a) **fatura mensal** da taxa de
plataforma (REQ-037, `[ASSUMIDO RN-025]`) com bloqueio por vencimento (F-03 E5); (b) **resolução
financeira de disputas** (REQ-039 — 2 procedentes/30d → modalidade direta bloqueada 90 dias, RN-027) —
a fatia deferida da Phase 13; (c) **saques** do entregador (REQ-038, `[ASSUMIDO R$ 20]`); (d)
**conciliação diária** (REQ-040) estendendo `reconcile.py`; (e) UI telas 08/15/16. **Tudo atrás de
interface própria (`PaymentPort`) com Stub** (DEC-003) — trocar PSP/ajustar não pode doer.
</domain>

<decisions>
## Implementation Decisions

### Fatura mensal (REQ-037, RN-025)
- **D-01:** Job arq fecha a fatura no **dia 1º** (aware-UTC, idempotente — 1 fatura/loja/competência),
  somando as taxas de plataforma das entregas diretas do mês (a entrega já **registra** a taxa efetiva
  — Phase 10 comentou "the effective charge is the Phase 11 invoice"). Tabela `platform_invoices` +
  `invoice_line_items` (area-scoped, money em centavos inteiros, FK RESTRICT).
- **D-02:** **Bloqueio por vencimento (F-03 E5):** fatura vencida **> 7 dias** → criação de entrega
  bloqueada para a loja. Reusa o ponto de guard já existente em `deliveries.service` (o subscription
  guard SAAS-BILLING §9) — adiciona a checagem de fatura vencida no MESMO lugar.

### Resolução financeira de disputas (REQ-039, RN-027)
- **D-03:** Estende `PaymentDispute` (Phase 9) com a **decisão financeira**: procedente/improcedente
  (a UI de triagem é da Phase 13; aqui entra a **consequência**). **2 procedentes em 30 dias →
  modalidade direta bloqueada 90 dias** para o entregador (RN-027). Bloqueio auditado + job que expira
  o bloqueio em 90d. Disputa procedente pode gerar ajuste financeiro (estorno/crédito via `PaymentPort`).

### Saques (REQ-038, R$ 20)
- **D-04:** Entregador saca do saldo de escrow liberado. **Saque < R$ 20 → rejeitado** (`[ASSUMIDO]`
  parametrizado, seed). `withdrawals` (area-scoped). Repasse via **novo método do `PaymentPort`**
  (`transfer_to_subaccount`/`payout`) — `[ASSUMIDO]` endpoint Safe2Pay (TD), Stub no dev/test.
  **Saque falha → saldo restituído** (transação compensatória, idempotente).

### Conciliação diária (REQ-040)
- **D-05:** Job diário estende `payments/reconcile.py`: cruza escrow/charges/repasses/estornos com o
  extrato do PSP (Stub no dev/test); divergência → registro + alerta (observability). Idempotente.

### UI (telas 08/15/16)
- **D-06:** Tela 15 (fatura da loja: extrato + status + vencimento + pagar), 16 (extrato/saldo do
  entregador + solicitar saque, R$ 20 mínimo citado), 08 (confirmação/recibo de pagamento direto).
  Reusa jx-data-table, payment-checkout-ux, trust-safety-ux. pt-BR.

### Valores parametrizados (DRV-009)
- **D-07:** Mínimo de saque, prazo de vencimento, taxa de plataforma, janela de disputa (30d/90d) são
  **seeds editáveis** `[ASSUMIDO]`, nunca hardcoded. Revenue share % (TD-13-01) **agora tem efeito
  financeiro** — confirmar valor com o dono antes do go-live.

### Claude's Discretion
- Layout fino das telas, formato do número da fatura, organização das linhas de conciliação.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Billing (LEI — CLAUDE.md §18)
- `docs/SAAS-BILLING-DOCS.md` — padrão canônico de billing/subscription/fatura (OBRIGATÓRIO seguir)
- skill `domain/saas-billing-canonical` — **obrigatória** (gate billing)
- skill `domain/safe2pay-escrow-br` (546 linhas) — **obrigatória** (escrow, split, repasse, estorno)

### Decisões e regras
- `.planning/DECISIONS.md` — ADR-009 v2 (Safe2Pay, escrow 24h) · ADR-012 (pagamento direto 1ª classe,
  taxa em fatura mensal, disputa mediada) · DEC-003 (suposições Safe2Pay) · DEC-004 (esta phase pós-deploy)
- `.planning/ROADMAP.md` — Phase 15 (REQs 035/037/038/039/040/012; verificações; wireframes 08/15/16)
- `.planning/TECH-DEBT.md` — TD-10-01..04 (cutover contrato) · TD-13-01 (revenue share %, agora com efeito)
- RN-025 (fatura) · RN-026 (confirmação direto) · RN-027 (disputa/bloqueio) · `projeto/regras-negocio/fluxos.md:142-152`

### Padrões de código a reusar (Phase 10/9)
- `apps/api/app/payments/` — `port.py` (PaymentPort — ADICIONAR `payout`/`transfer`), `escrow.py`,
  `fees.py`, `reconcile.py`, `factory.py`, `safe2pay_stub.py`/`safe2pay_adapter.py`
- `apps/api/app/payments_direct/models.py` — `PaymentDispute`, `DirectPaymentConfirmation`
- `apps/api/app/deliveries/service.py:313` — guard de criação (subscription) — adicionar fatura vencida
- `app/workers/` — jobs arq aware-UTC idempotentes (fatura dia 1º, conciliação diária, expira bloqueio 90d)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PaymentPort` já abstrai o PSP — saque adiciona um método de repasse (payout) ao Port + Stub + adapter.
- `escrow.py` + escrow_ledger (Phase 10) — saldo do entregador para saque vem daí.
- `reconcile.py` já existe — conciliação diária é extensão, não do zero.
- Guard de criação em `deliveries.service` já existe (subscription) — fatura vencida entra no mesmo ponto.
- `PaymentDispute` já existe — só adiciona a decisão/consequência financeira.

### Established Patterns
- Money em **centavos inteiros**; idempotência por `Reference`/UNIQUE; webhook dedup por IdTransaction
  (Phase 10). Tudo atrás de `PaymentPort` com Stub. Valores `[ASSUMIDO]` em seed.

### Integration Points
- Novos routers em `app/api/v1/router.py` (bloco Phase 15). Jobs em `workers/settings.py`.
- Telas 15/16/08 no shell de loja e de entregador (existentes).
</code_context>

<specifics>
## Specific Ideas
- Esta é a phase que **liga o dinheiro** do que estava só registrado: a taxa que a entrega anotou vira
  fatura; a disputa que era triagem vira consequência; o saldo de escrow vira saque.
- Honestidade: tudo verde com Stub; produção exige o contrato (TD-10-01..04) — o RELEASE-CHECKLIST já marca.
</specifics>

<deferred>
## Deferred Ideas
- Antecipação de recebíveis / parcelamento da fatura — backlog.
- Score com consequência financeira — v1.1 (ADR-013).
</deferred>

---

*Phase: 15-safe2pay-financeiro-back-office*
*Context gathered: 2026-06-11*
