# CORRECAO-130 — Estimativa de frete filtra por equipe selecionada

## O que mudou

### Backend (apps/api)
- **deliveries/router.py**: Endpoint GET `/v1/deliveries/estimate` agora aceita `team_id` (query param opcional)
- **deliveries/estimate.py**: `eligible_online_prices_cents` aceita `team_id`. Quando não é null, filtra couriers por `Courier.team_id == team_id`

### Frontend (apps/web)
- **delivery.service.ts**: `estimate()` agora aceita `teamId` opcional e envia como query param
- **nova-entrega.page.ts**: `loadEstimate` recebe `teamId`. Ao trocar equipe (`team_id.valueChanges`), recalcula a estimativa. Ao trocar bairro, passa a equipe atual

## Arquivos alterados
- apps/api/app/deliveries/router.py
- apps/api/app/deliveries/estimate.py
- apps/web/src/features/loja/entregas/delivery.service.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
