# CORRECAO-218 — Localização do entregador para ranking do dispatch

**Data:** 2026-07-08

## Problema
O dispatch rankeava entregadores usando `distance_m` (distância pickup→dropoff), que é igual para todos os candidatos — o critério de ETA era fictício.

## Solução

### Backend

**`0040_courier_location.py`** (migration)
- Colunas `lat FLOAT`, `lng FLOAT`, `location_at DATETIME(tz)` adicionadas em `couriers`

**`couriers/models.py`**
- Campos `lat`, `lng`, `location_at` adicionados ao modelo `Courier`

**`couriers/schemas.py`**
- `CourierLocationBody`: `{ lat: float, lng: float }`

**`couriers/router.py`**
- `PATCH /v1/couriers/{id}/location`: grava posição somente se `is_online=true`; ignora silenciosamente se offline

**`dispatch/cascade.py`**
- `build_candidates` aceita `merchant_lat`, `merchant_lng` opcionais
- Quando courier tem posição conhecida: `eta_s = haversine(courier → merchant)` (real)
- Fallback para `distance_m` quando posição não disponível

**`workers/dispatch.py`**
- `_merchant_coords()`: helper que carrega `lat`/`lng` do merchant
- Passa `merchant_lat`/`merchant_lng` nas 3 chamadas de `build_candidates`

### Frontend

**`courier-location.service.ts`** (novo)
- Intervalo: 5 min (`300_000ms`)
- Filtro de movimento: 100m (reutiliza `haversineMeters` do `location-polling.service`)
- Usa `getCurrentPosition` one-shot (não `watchPosition`)
- `start(courierId)` / `stop()`

**`inicio.page.ts`**
- Injeta `CourierLocationService`
- `ngOnInit`: se `profile.is_online`, chama `locationSvc.start(id)`
- `_applyAvailability`: `start()` ao ficar online, `stop()` ao ficar offline ou em erro
- Timer `online_until`: `stop()` quando expirar automaticamente
