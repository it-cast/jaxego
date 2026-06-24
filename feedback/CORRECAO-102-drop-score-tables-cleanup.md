# Correção 102 — Drop das tabelas de score e limpeza de código morto

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Migration

- `apps/api/alembic/versions/0018_drop_score_tables.py` (criado) — dropa `courier_score_snapshots` e `score_weights`

### Backend — código morto removido

- `apps/api/app/scores/service.py` — esvaziado (build_snapshot, latest_snapshot, seed_score_weights removidos)
- `apps/api/app/scores/models.py` — esvaziado (CourierScoreSnapshot, ScoreWeight removidos)
- `apps/api/app/scores/schemas.py` — esvaziado (CourierScoreRead, ScoreComponentRead removidos)
- `apps/api/app/scores/signals.py` — esvaziado (derive_signals removido)
- `apps/api/app/workers/scores.py` — esvaziado (snapshot_scores removido)

## O que foi removido

- Tabelas `courier_score_snapshots` e `score_weights` dropadas via migration 0018
- Models, service, schemas, signals e worker associados esvaziados
- Cron `snapshot_scores` já tinha sido removido do settings na correção 101

## O que permanece

- `courier_ratings` — tabela de avaliações (fonte de verdade)
- `scores/router.py` — calcula média em tempo real dos últimos 90 dias
- Módulo `scores/` mantido como pacote (router ativo, demais arquivos vazios)
