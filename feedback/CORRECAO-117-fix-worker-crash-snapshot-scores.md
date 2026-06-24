# CORRECAO-117 — Fix worker crashando por referência a snapshot_scores removido

## O que mudou

### Backend (apps/api)
- **workers/settings.py**: Removida referência a `snapshot_scores` na lista de functions do worker. Essa função foi removida na CORRECAO-102 (simplificação do score para média em tempo real) mas a referência no settings não foi removida junto, causando `NameError` e impedindo o worker de iniciar. Sem o worker, nenhuma entrega era despachada para entregadores.

## Arquivos alterados
- apps/api/app/workers/settings.py
