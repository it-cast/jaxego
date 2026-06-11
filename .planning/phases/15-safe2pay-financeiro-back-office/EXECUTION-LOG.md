# Phase 15 — EXECUTION-LOG (backend, Waves 1-2 / T-01..T-07)

**Executor:** backend (apps/api). Escopo: Waves 1-2 (T-01..T-07). NÃO inclui frontend (Wave 3) nem T-11 (integration check).
**Resultado:** `uv run pytest -m "not mysql"` → **494 passed, 23 deselected**. `uv run ruff check .` → **limpo**.

## Tasks concluídas

| Task | Descrição | Commit |
|------|-----------|--------|
| T-01 | Migration 0013 + modelos (platform_invoices, invoice_line_items, withdrawals, dispute_blocks) + decisão financeira em payment_disputes; teste @mysql de reversibilidade | feat(15) T-01 |
| T-02 | invoices/: fatura mensal por (loja, competência), idempotente; agrega taxa registrada nas entregas diretas; status aberto/vencida/paga; pagar via PaymentPort | feat(15) T-02/T-03 |
| T-03 | Guard F-03 E5: fatura vencida >7d bloqueia criação no mesmo ponto do subscription guard (402) | feat(15) T-02/T-03 |
| T-04 | Decisão financeira da disputa: procedente → ajuste via PaymentPort.refund/crédito, auditado; improcedente não move dinheiro | feat(15) T-04/T-05 |
| T-05 | RN-027: 2 procedentes/30d → dispute_blocks 90d (modalidade direta bloqueada) + job de expiração; clock controlado | feat(15) T-04/T-05 |
| T-06 | withdrawals/: saque do saldo escrow liberado (SELECT FOR UPDATE), mín. R$ 20 (seed), repasse via novo PaymentPort.payout, falha→restitui, idempotência por reference | feat(15) T-06 |
| T-07 | Conciliação diária estendida (charges + repasses × extrato); divergência → alerta structlog; routers Phase 15 montados | feat(15) T-07 |

## Desvios da plano (Regras 1-3 — auto-fix)

- **[Rule 2 — Missing critical functionality] Registro de `fee_cents` em entrega direta.**
  - **Onde:** T-02, `deliveries/service.py:create_delivery`.
  - **Motivo:** a entrega direta nascia com `fee_cents=0` (a taxa só era gravada para card/pix). Sem o registro, a fatura mensal (que DERIVA das entregas diretas — D-01/TH-03) não teria dado nenhum. Passei a gravar `delivery.fee_cents = plan.fee_cents` na criação de entrega direta (derivado do plano ativo, nunca input do usuário).
  - **Impacto:** o invoice agrega corretamente; coberto pelos testes de fechamento de fatura.

- **[Rule 2 — Missing critical functionality] Guard de modalidade direta bloqueada (RN-027/TH-08).**
  - **Onde:** T-05, `payments_direct/service.py:confirm_direct_payment`.
  - **Motivo:** o `DisputeBlock` precisava de um ponto de enforcement server-side. Adicionei o guard `is_blocked` em `confirm_direct_payment` (403) — o courier bloqueado não opera a modalidade direta. Coberto por teste.

- **[Rule 3 — Wiring] Crons Phase 15 + conciliação financeira diária registrados em `workers/settings.py`.**
  - close_platform_invoices (dia 1º), mark_invoices_overdue, expire_dispute_blocks, reconcile_finance_daily — aware-UTC, idempotentes.

## Decisões de implementação

- **Repasse do saque** isolado no novo método `PaymentPort.payout` (Stub determinístico + adapter `[ASSUMIDO]` com endpoint `/v2/marketplace/transfer`). Registrado como **TD-15-01** (pre_launch_high — cutover depende do contrato).
- **Pagamento de fatura** via `charge_with_split` com um único leg ao recipient da plataforma (mantém o invariante `amount == Σ splits` do Stub; sem método novo no Port).
- **Conciliação** keyada por `transaction_id`; cruza `platform_charges` pagos + `withdrawals` pagos × extrato do PSP Stub. Divergência (>R$0,01 ou ausente em um lado) → ERROR log (alerta), nunca auto-corrige (TH-I).
- **Valores parametrizados** (D-07 / DRV-009): `invoice_due_days`, `invoice_overdue_block_days`, `withdrawal_min_cents` (2000 = R$ 20), `dispute_block_threshold/window_days/duration_days` em `core/config.py` (seed-editáveis), nunca hardcoded.

## Segurança (Gate 4/8) — atendido

- TH-01 saque escopado a (area_id, courier_id) → saldo IDOR = 0. TH-02 `SELECT ... FOR UPDATE` no saldo + reference UNIQUE. TH-03 fatura derivada das entregas (não input). TH-05 bloqueio e decisão auditados (audit_log append-only). TH-07 nunca move dinheiro sem confirmação (refund/payout via PaymentPort). TH-08 bloqueio de fatura e de modalidade server-side.
- TH-06 sem CPF/cartão/telefone em log (apenas ids/valores nos `logger.info`/audit payloads).

## Testes novos (Phase 15)

- `tests/invoices/test_invoice_close.py` (3) — fecha+soma, idempotência 1/loja/competência, pagar via Port.
- `tests/invoices/test_overdue_guard.py` (4) — vencida 8d bloqueia / 5d permite / sem fatura permite / mark_overdue.
- `tests/payments_direct/test_dispute_block.py` (6) — procedente ajusta+audita, improcedente não move, 2/30d→90d (clock), fora da janela não, expira 90d, courier bloqueado não confirma.
- `tests/withdrawals/test_withdrawal.py` (7) — saldo, <R$20, >saldo, sucesso debita, falha restitui, idempotência, IDOR→0.
- `tests/payments/test_reconcile_daily.py` (3) — payout casa / diverge / ausente do extrato.
- `tests/db/test_migration_0013.py` (1, @mysql) — reversibilidade upgrade→downgrade→upgrade.

## Pendências (fora do escopo deste executor)

- Wave 3 (frontend telas 08/15/16) — NÃO feito (outro executor).
- T-11 (integration check / Gate 5) — NÃO feito.
- Teste @mysql 0013 escrito mas NÃO executado (rodar `-m mysql` contra MySQL 8 real).
- TD-15-01 (cutover do repasse) — bloqueia deploy de produção do saque; tudo verde com Stub.
