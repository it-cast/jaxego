# CORRECAO-187 — Geocoding Mapbox para resolução de zona_id na entrega

## Problema
Nominatim (OSM) não tem cobertura de ruas de cidades pequenas brasileiras (ex: Santo Antônio de Pádua) — retorna `[]` para endereços específicos. `zona_id` nunca era gravado nas entregas.

## Solução

### `app/integrations/geocoding_mapbox.py` (NOVO)
Adapter Mapbox Geocoding API v5:
- Endpoint: `/geocoding/v5/mapbox.places/{query}.json`
- Parâmetros: `country=BR`, `language=pt`, `limit=1`
- Resposta: `features[0].center` = `[lng, lat]` (GeoJSON order)
- SSRF-guard via `assert_safe_url` (allowlist: `api.mapbox.com`)
- Falhas retornam `None` sem lançar exceção

### `app/core/config.py`
Adicionado campo `mapbox_token: str | None = Field(default=None)`.
Lido da variável de ambiente `MAPBOX_TOKEN`.

### `app/integrations/factory.py`
`get_geocoding_adapter()` agora usa Mapbox quando `settings.mapbox_token` estiver configurado, caso contrário cai no Nominatim (comportamento anterior).

## Configuração
Adicionar no `.env` da API:
```
MAPBOX_TOKEN=pk.eyJ1Ijoi...
```

## Fluxo na criação de entrega
`create_delivery()` → sem lat/lng no body → monta endereço (`rua, numero, bairro, cidade`) → `get_geocoding_adapter().geocode(address)` → Mapbox retorna lat/lng → `find_zona_id()` point-in-polygon → `delivery.zona_id` gravado.
