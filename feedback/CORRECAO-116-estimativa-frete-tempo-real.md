# CORRECAO-116 — Estimativa de frete em tempo real ao selecionar bairro

## O que mudou

### Backend (apps/api)
- **deliveries/router.py**: Novo endpoint GET `/v1/deliveries/estimate?dropoff_neighborhood_id=N` que retorna `{ estimate_min_cents, estimate_max_cents, courier_count }`. Usa a mesma lógica de `eligible_online_prices_cents` + `median_cents` que o create já usava.

### Frontend (apps/web)
- **delivery.service.ts**: Novo método `estimate(dropoffNeighborhoodId)` que chama o endpoint de estimativa.
- **nova-entrega.page.ts**: Ao selecionar um bairro de entrega, chama `loadEstimate()` automaticamente. O `jx-estimate-box` agora mostra o frete estimado e a quantidade de entregadores antes do submit. Warning de "0 entregadores" também ativado em tempo real.

## Arquivos alterados
- apps/api/app/deliveries/router.py
- apps/web/src/features/loja/entregas/delivery.service.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
