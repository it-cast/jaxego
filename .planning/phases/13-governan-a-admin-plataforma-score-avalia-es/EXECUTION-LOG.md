# Phase 13 — Execution Log (backend, Waves 1-2 / T-01..T-08)

**Executor:** backend (apps/api) · **Escopo:** Waves 1-2 (T-01..T-08). Frontend (Wave 3) NÃO executado.
**Data:** 2026-06-11 · **Branch:** master · **Migration:** 0011

## Tarefas concluídas

| Task | Descrição | Commit |
|------|-----------|--------|
| T-01 | Migration 0011 + modelos (scores/ratings/suspensions/revenue_share) | `1ec44f9` |
| T-02 | Score explicável: composição parametrizada, snapshot diário idempotente, endpoints | `96be4e3` |
| T-04 | Isolamento ADR-013 (score × dispatch/ranking) — teste | `96be4e3` |
| T-03 | Avaliações loja→entregador pós-FINALIZADA (UNIQUE/escopo) | `5ab3d42` |
| T-05/06/07/08 | Suspensão/recurso + reversão SLA + disputas + admin plataforma | `ddafcc6` |

## Decisões de implementação (Claude's discretion — registradas)

- **Composição do score:** soma ponderada `raw(0..1) × peso(seed) × 100`; pesos seed
  somam 1.0 (acceptance .25 / punctuality .25 / proof_ok .20 / low_cancellation .15 /
  ratings .15). Bandas de nível: diamante≥90, ouro≥75, prata≥55, bronze≥35, probation≥0.
  Tudo parametrizável (DRV-009) — bandas são banda de apresentação, sem efeito financeiro.
- **Sinais do score:** derivados de dados existentes (ratings avg + razão de conclusão de
  entregas). `acceptance_rate`/`punctuality` usam proxy de conclusão no M1 (ver TD-13-02).
  Prior neutro 0.5 para entregador sem histórico (não pune novato).
- **SLA de recurso:** janela default 72h (`[ASSUMIDO]`, parametrizável). Reversão por job
  marca `reverted_at` (idempotente). Teste com clock controlado via `sla=timedelta(hours=-1)`
  para forçar vencido sem mexer no relógio do sistema.
- **Revenue share:** seed `[ASSUMIDO]` 10% (TD-13-01). Tabela versionada por `effective_from`
  (estilo ADR-103). Endpoint de escrita auditado; NÃO move dinheiro (DEC-004 → Phase 15).
- **Disputas (T-06):** decisão administrativa marca `payment_dispute.status=resolved` +
  audit; placeholder explícito de comentário no service para a consequência financeira da
  Phase 15 (bloqueio 90d/restituição NÃO implementados).

## Segurança (Gate 4 — TH-01..TH-08)

- TH-01 TOTP: reusa `require_platform_admin` (bloqueio sem TOTP testado via HTTP).
- TH-02 cross-área: cada leitura do platform_admin grava audit_log `cross_area_bypass=True` (testado).
- TH-03 suspensão append-only: transições via audit_log (trigger MySQL já bloqueia UPDATE/DELETE).
- TH-04 require_role/require_platform_admin em todos os endpoints (admin_area não acessa platform — testado).
- TH-05 score read-only: NENHUM endpoint de escrita de nota; snapshot derivado pelo job.
- TH-06 filtros bound: Pydantic/Query + LIKE parametrizado (teste com payload de injection).
- TH-07 PII fora de log: agregados de score usam só counts/stars; audits só ids/states.
- TH-08 reversão idempotente: aware-UTC, `reverted_at` guard (testado idempotência).

## Desvios das regras (deviation rules)

- **[Rule 3]** A migration 0011 precisou registrar os novos mappers em `tests/conftest.py`
  para o `Base.metadata.create_all` do SQLite enxergar as tabelas (bloqueava import dos testes).
- Nenhum desvio arquitetural (Rule 4). Nenhum bug pré-existente corrigido fora de escopo.

## Tech debt registrada

- **TD-13-01** (pre_launch_high) — revenue share % `[ASSUMIDO]` 10%, decisão do dono antes da Phase 15.
- **TD-13-02** (post_launch_quarter) — proxies de sinal de score (acceptance/punctuality) para v1.1.

## Itens NÃO executados (fora de escopo deste executor)

- Wave 3 (frontend T-09..T-12) — admin plataforma 23-25 + área 09/19/20.
- Consequência financeira de disputa/score (Phase 15 / DEC-004).
- Teste `@pytest.mark.mysql` da migration 0011 escrito mas NÃO rodado aqui (roda contra MySQL live).
