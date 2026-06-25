# CORRECAO-139 — Campo price_cents na entrega (preço real do entregador)

## O que mudou

### Backend (apps/api)
- **deliveries/models.py**: Adicionado `price_cents` (Integer, nullable) — preenchido com o preço real do entregador quando ele aceita a oferta
- **alembic 0025**: Migration para adicionar coluna `price_cents`
- **deliveries/schemas.py**: Todos os schemas de delivery (DeliveryOut, CreateDeliveryResponse, DeliveryListItem, CourierDeliveryOut, CourierDeliveryListItem) agora incluem `price_cents`
- **deliveries/router.py**: Serialização inclui `price_cents`
- **couriers/router.py**: Serialização inclui `price_cents`
- **dispatch/service.py**: No `accept_offer`, calcula o preço real do entregador via `effective_price_cents` e salva em `delivery.price_cents`

### Frontend
- **delivery.models.ts** (packages/shared): `CreateDeliveryResponse` e `DeliveryListItem` incluem `price_cents`
- **dashboard.page.ts** (apps/web): Cálculo de frete do dia usa `price_cents` (fallback para `estimate_min_cents`)

## Fluxo
1. Entrega criada → `estimate_min/max_cents` = mediana (para referência)
2. Entregador aceita → `price_cents` = preço real dele para aquele bairro
3. Frontend exibe `price_cents` quando disponível

## Arquivos alterados
- apps/api/app/deliveries/models.py
- apps/api/alembic/versions/0025_delivery_price_cents.py (novo)
- apps/api/app/deliveries/schemas.py
- apps/api/app/deliveries/router.py
- apps/api/app/couriers/router.py
- apps/api/app/dispatch/service.py
- packages/shared/src/shared/models/delivery.models.ts
- apps/web/src/features/loja/dashboard/dashboard.page.ts
