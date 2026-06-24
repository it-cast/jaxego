# Correção 100 — Score do entregador calculado em tempo real

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/api/app/scores/router.py` — endpoint `GET /v1/couriers/{id}/score` reescrito

## Problema

O score do entregador dependia de um cron diário (`snapshot_scores` às 05:00 UTC) que gravava snapshots. Após uma avaliação, o entregador só veria o score atualizado no dia seguinte. E o script one-shot falhava por problemas de lazy-loading do SQLAlchemy.

## Correção

- Endpoint `GET /v1/couriers/{id}/score` agora calcula o score em tempo real:
  - Média das estrelas das `courier_ratings` × 20 (escala 0-100)
  - Contagem de entregas finalizadas
  - Contagem de avaliações recebidas
  - Level derivado do score: diamante (≥90), ouro (≥70), prata (≥50), bronze (≥30), probation (<30)
- Sem dependência de snapshot — score atualizado imediatamente após avaliação
- Se não tem avaliações, retorna score 0 com level "probation" (sem 404)
