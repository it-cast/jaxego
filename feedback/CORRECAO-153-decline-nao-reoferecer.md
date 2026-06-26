# CORRECAO-153 — Entregador que recusou não recebe a mesma entrega novamente

## O que mudou

### Backend (apps/api)
- **dispatch/offer_state.py**: Novas funções `add_declined`, `get_declined`, `clear_declined` que gerenciam um Redis SET `dispatch:{delivery_id}:declined` com TTL de 24h
- **dispatch/cascade.py**: 
  - `advance_after_decline` agora chama `add_declined` para registrar quem recusou
  - `build_candidates` aceita `excluded_ids` e filtra esses couriers da fila
- **workers/dispatch.py**: Ao rebuildar a fila de candidatos, busca os declined no Redis e passa como `excluded_ids`

## Fluxo
1. Entregador recusa → `add_declined(delivery_id, courier_id)` salvo no Redis
2. Cascade avança para o próximo
3. Se a fila acabar e o cron `redispatch_stale_deliveries` rebuildar, os que recusaram são excluídos
4. O set expira em 24h automaticamente

## Arquivos alterados
- apps/api/app/dispatch/offer_state.py
- apps/api/app/dispatch/cascade.py
- apps/api/app/workers/dispatch.py
