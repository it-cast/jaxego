# CORRECAO-140 — Remover estimate_min_cents e estimate_max_cents

## O que mudou

### Backend (apps/api)
- **alembic 0026**: Drop colunas `estimate_min_cents` e `estimate_max_cents` da tabela deliveries
- **deliveries/models.py**: Campos removidos do modelo
- **deliveries/schemas.py**: Campos removidos de todos os schemas (DeliveryOut, CreateDeliveryResponse, DeliveryListItem, CourierDeliveryOut, CourierDeliveryListItem)
- **deliveries/router.py**: Serialização removida. Endpoint `/estimate` agora retorna `price_cents` em vez de `estimate_min/max`
- **deliveries/service.py**: Criação não seta mais estimate. Cancelamento usa `price_cents`. Response usa `price_cents`
- **couriers/router.py**: Serialização de delivery removida
- **dispatch/service.py**: Fallback usa `price_cents` em vez de `estimate_max_cents`
- **api_public/schemas.py** e **service.py**: Campos removidos

### Frontend
- **delivery.models.ts**: Campos `estimate_min_cents`/`estimate_max_cents` removidos de todas as interfaces
- **dashboard.page.ts**: Usa `price_cents` direto

## Arquivos alterados
- apps/api/alembic/versions/0026_drop_estimate_columns.py (novo)
- apps/api/app/deliveries/models.py
- apps/api/app/deliveries/schemas.py
- apps/api/app/deliveries/router.py
- apps/api/app/deliveries/service.py
- apps/api/app/couriers/router.py
- apps/api/app/dispatch/service.py
- apps/api/app/api_public/schemas.py
- apps/api/app/api_public/service.py
- packages/shared/src/shared/models/delivery.models.ts
- apps/web/src/features/loja/dashboard/dashboard.page.ts
