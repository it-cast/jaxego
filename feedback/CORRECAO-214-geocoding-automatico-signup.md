# CORRECAO-214 — Geocoding automático no signup

**Data:** 2026-07-08

## Problema

Ao cadastrar um estabelecimento digitando o endereço manualmente (sem clicar no botão de busca de endereço), os campos `lat` e `lng` não eram salvos no banco. Isso porque o geocoding só era disparado via GPS do browser, que dependia do usuário acionar o botão.

## Correção

**Arquivo:** `apps/api/app/merchants/service.py` — função `signup()`

Adicionada lógica de geocoding automático **no backend**, executada antes de criar o merchant:

1. Se `body.lat` e `body.lng` chegarem preenchidos (browser GPS acionado) → usa esses valores.
2. Se um ou ambos estiverem `None` → constrói string de endereço a partir dos campos disponíveis (`address`, `address_number`, `address_neighborhood`, `address_zip`, `address_state`, `"Brasil"`) e chama `geocoding.geocode(address)`.
3. Se o Nominatim retornar resultado → salva `lat`/`lng` no merchant.
4. Se falhar (provider down ou endereço não encontrado) → salva `NULL` (comportamento anterior), loga `geocoding_failed_on_signup`.

## Comportamento

- **GPS acionado:** lat/lng do browser (mais preciso — ponto exato da empresa).
- **Endereço digitado sem GPS:** lat/lng geocodificado pelo Nominatim (precisão de rua/bairro).
- **Endereço incompleto ou geocoding falhando:** `NULL` — sem bloquear o cadastro.

## Serviço de geocoding

Usa o `GeocodingPort` já injetado em `signup()`, implementado por `GeocodingHttpAdapter` (Nominatim/OSM). Nenhuma dependência nova.
