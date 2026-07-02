# CORRECAO-186 — zona_id na entrega + preço por zona no dispatch

## Problema
Ao criar uma entrega, a zona geográfica do endereço de entrega não era determinada,
e o dispatch exibia o preço da tabela de bairros/distância mesmo quando o entregador
ou equipe tinha preço configurado por zona.

## Solução

### 1. `areas/zona_finder.py` (NOVO)
Algoritmo ray-casting puro Python (teorema de Jordan) para determinar em qual zona
um ponto (lat, lng) está contido. Coordenadas GeoJSON são [lng, lat] — a função
converte corretamente.

### 2. `deliveries/models.py`
Adicionado campo `zona_id` (FK → `zonas.id`, SET NULL, nullable) ao modelo `Delivery`.

### 3. `alembic/versions/0034_delivery_zona_id.py`
Migration que adiciona coluna `zona_id` + FK + index em `deliveries`.

### 4. `deliveries/service.py` — `create_delivery()`
- Salva `pickup_lat/lng` e `dropoff_lat/lng` da requisição no `Delivery`
- Após `session.flush()` (delivery tem ID), chama `find_zona_id()` com os coords
  do dropoff e salva `delivery.zona_id`

### 5. `dispatch/service.py`
Nova helper `_zone_price_cents(session, courier_id, zona_id)`:
- Busca `CourierZona` → preço customizado do entregador para a zona
- Fallback: `TeamZona` → preço mínimo da equipe para a zona
- Fallback: retorna `None` → usa tabela antiga (`effective_price_cents`)

Atualizado em 4 pontos de resolução de preço:
- `build_offer_view()` — preço exibido na oferta ao entregador
- `accept_offer()` — `price_cents` gravado ao aceitar
- `self_assign_pool_delivery()` — idem para self-assign no pool
- `list_unanswered_pool()` — pré-carrega `cz_map`/`tz_map` (sem N+1), usa `_price(d)`

## Hierarquia de preços
`CourierZona.preco_cents` → `TeamZona.preco_minimo_cents` → `effective_price_cents` (tabela legada)

## Migration aplicada
`0033_courier_zona` → `0034_delivery_zona_id` ✅
