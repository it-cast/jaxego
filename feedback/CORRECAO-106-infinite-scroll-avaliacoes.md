# CORRECAO-106 — Infinite scroll na lista de avaliações do entregador

## O que mudou

### Backend (apps/api)
- **scores/router.py**: Endpoint GET `/v1/couriers/{id}/ratings` agora aceita `limit` e `offset` (default 10/0). Retorna `{ items: [...], total: N }` em vez de array direto.

### Frontend (apps/app)
- **avaliacoes.page.ts**: Implementado infinite scroll com `IonInfiniteScroll`. Carrega 10 avaliações por vez, busca mais ao rolar até o final. Filtro por estrelas aplicado sobre os registros já carregados.
- **entregador.service.ts**: `listRatings` agora aceita `limit`/`offset` e retorna `{ items, total }`. Interface `RatingItem` exportada do service (removida duplicação local na page).

## Arquivos alterados
- apps/api/app/scores/router.py
- apps/app/src/features/entregador/perfil/avaliacoes.page.ts
- apps/app/src/features/entregador/entregador.service.ts
