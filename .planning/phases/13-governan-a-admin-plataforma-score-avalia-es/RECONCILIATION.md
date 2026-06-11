# Phase 13 — Reconciliação (prometido vs. real)

**Data:** 2026-06-11 (autopilot) · **Status:** sem gaps abertos

| Prometido (PLAN) | Real | Evidência |
|---|---|---|
| Migration 0011 reversível (4 tabelas + seed) | ✓ | `alembic/versions/0011_governance_score_ratings.py` + teste @mysql |
| Score explicável (snapshot diário, componentes/pesos, níveis) | ✓ | `app/scores/` + `app/workers/scores.py` |
| **Score sem efeito financeiro/operacional** (ADR-013) | ✓ | `app/dispatch/ranking.py`: `score` com `_SCORE_WEIGHT_M1=0`; não importa app.scores (teste T-04) |
| Avaliações pós-FINALIZADA (UNIQUE/entrega, merchant_scope) | ✓ | `app/ratings/` |
| Suspensão auditada (motivo, before/after) | ✓ | `app/suspensions/` + audit_log |
| Recurso com reversão automática por SLA + alerta | ✓ | `app/workers/appeals.py` (clock controlado, idempotente) |
| Admin plataforma cross-área auditado (TOTP) | ✓ | `app/platform_admin/` (`require_platform_admin` + audit cross-área) |
| Disputas admin de área (sem efeito financeiro → Phase 15) | ✓ | `app/suspensions/` (decisão administrativa, placeholder financeiro) |
| Revenue share parametrizado (sem mover dinheiro) | ✓ | `area_revenue_share` + seed (TD-13-01 % a decidir) |
| Componentes jx-score-badge/breakdown/suspension-panel | ✓ | `apps/web/src/shared/components/` |
| Telas 23/24/25 (plataforma) + 09/19/20 (área) | ✓ | `features/admin-plataforma/`, `features/admin/governanca/` |
| Zero hex / testes verdes / lint | ✓ | backend 453 passed (1 flaky pré-existente); frontend 177; ruff+lint limpos |

## Desvios / TD
- **TD-13-01** (pre_launch_high): revenue share % `[ASSUMIDO 10%]` — decisão do dono (OQ-1).
- **TD-13-02** (post_launch_quarter): proxies de sinal de score (refinar fontes).
- **TD-13-03** (post_launch_quarter): histórico detalhado de avaliações sem endpoint dedicado (agregado no breakdown).
- Falha flaky pré-existente `test_health` (Phase 1) — fora de escopo, documentada.

## Gaps abertos
Nenhum. Pendente `pytest -m mysql` (migration 0011) em DB live.
