# Correção 101 — Score simplificado para média de avaliações dos últimos 90 dias

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend

- `apps/api/app/scores/router.py` — reescrito: ambos endpoints (entregador e admin) calculam média de `courier_ratings` dos últimos 90 dias em tempo real
- `apps/api/app/workers/settings.py` — cron `snapshot_scores` removido
- `apps/api/app/platform_admin/service.py` — busca de score trocada de `CourierScoreSnapshot` para `AVG(courier_ratings.stars)`

### Frontend (App)

- `apps/app/src/features/entregador/entregador.service.ts` — interface `CourierScore` simplificada para `{ avg_stars, total_ratings }`; `ScoreComponent` removido
- `apps/app/src/features/entregador/perfil.page.ts` — removidos `ScoreChipComponent`, `ScoreBreakdownComponent`, `ScoreLevel`, `VALID_LEVELS`, `level` computed; exibe "4.5 ★ (12 avaliações)"
- `apps/app/src/features/entregador/inicio.page.ts` — removidos `ScoreChipComponent`, `ScoreLevel`, `VALID_LEVELS`, `level` computed; exibe "4.5 ★"

## O que foi removido

- Dependência do cron diário `snapshot_scores`
- Tabelas `courier_score_snapshots` e `score_weights` não são mais lidas (podem ser dropadas em migration futura)
- Componentes `ScoreChipComponent` e `ScoreBreakdownComponent` não são mais usados no app

## Como funciona agora

- API retorna `{ avg_stars: 4.5, total_ratings: 12 }` calculado em tempo real
- Filtro: avaliações dos últimos 90 dias
- Score atualizado imediatamente após nova avaliação
