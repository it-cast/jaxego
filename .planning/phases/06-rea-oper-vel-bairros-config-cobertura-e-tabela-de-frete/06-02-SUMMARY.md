---
phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
plan: 02
subsystem: backend (neighborhoods catalog + spatial)
tags: [spatial, neighborhoods, st_contains, geojson, area-scoped]
requires:
  - "Plan 01 migration 0005 (neighborhoods_catalog + polygon POLYGON NULL SRID 4326)"
provides:
  - "módulo app/neighborhoods/ (models/schemas/spatial/service/router)"
  - "spatial.point_in_polygon (ST_Contains, lat-first) — primitivo de elegibilidade da Phase 8"
  - "validate_polygon_geojson (shapely anti-DoS)"
  - "/v1/neighborhoods (CRUD area-scoped)"
affects:
  - "apps/api/app/api/v1/router.py (registra neighborhoods)"
  - "apps/api/tests/conftest.py (registra mapper Neighborhood)"
tech-stack:
  added: [shapely]
  patterns:
    - "func.ST_* nativo (sem GeoAlchemy2 — LOW-1); polygon fora do ORM"
    - "validação server-side de GeoJSON antes do DB (anti-DoS)"
key-files:
  created:
    - apps/api/app/neighborhoods/__init__.py
    - apps/api/app/neighborhoods/models.py
    - apps/api/app/neighborhoods/schemas.py
    - apps/api/app/neighborhoods/spatial.py
    - apps/api/app/neighborhoods/service.py
    - apps/api/app/neighborhoods/router.py
  modified:
    - apps/api/app/api/v1/router.py
    - apps/api/tests/conftest.py
    - apps/api/tests/neighborhoods/test_models.py
    - apps/api/pyproject.toml
decisions:
  - "polygon manipulado só via func.ST_*/text (LOW-1 — sem GeoAlchemy2)"
  - "remove_neighborhood usa cobertura/preço como proxy de 'entregas ativas' até a Phase 7"
metrics:
  duration: ~35min
  tasks: 2
  files: 10
  completed: 2026-06-10
---

# Phase 6 Plan 02: Catálogo de bairros + ST_Contains Summary

Módulo `app/neighborhoods/` completo: CRUD area-scoped de bairros (bairro por nome é válido; polígono GeoJSON opcional validado por shapely e persistido via `ST_GeomFromGeoJSON`), o helper único `spatial.py` que centraliza o eixo lat-first (Pitfall 2) e o `point_in_polygon` (`ST_Contains`) que a Phase 8 consumirá para elegibilidade — tudo nativo via `func.ST_*` sem GeoAlchemy2 (LOW-1).

## Tasks Completed

| Task | Nome | Commit | Arquivos-chave |
|------|------|--------|----------------|
| 1 | Models + schemas + spatial + validação | 964ab8d | models.py, schemas.py, spatial.py |
| 2 | Service CRUD area-scoped + router | cb56f50 | service.py, router.py, v1/router.py |

## Decisões / notas

- **`polygon` fora do ORM** (LOW-1): a coluna existe só no MySQL (DDL 0005) e é lida/escrita exclusivamente via `func.ST_*`/`text` (binds parametrizados — A03). Em SQLite a coluna não existe → asserções espaciais só `@pytest.mark.mysql`.
- **`spatial.py` é o dono único do eixo** (Pitfall 2): `ST_GeomFromGeoJSON` reordena GeoJSON→4326 sozinho; `point_in_polygon` monta `POINT(lat lng)` (lat primeiro) via `ST_GeomFromText(CONCAT('POINT(', :lat, ' ', :lng, ')'), 4326)`.
- **`remove_neighborhood`**: a tabela de entregas chega na Phase 7; o guard de M1 bloqueia a remoção quando o bairro é referenciado por cobertura/preço (proxy de "em uso") com a mensagem exata do wireframe (409). Ver SUGGESTIONS.

## Deviations from Plan

- **[Rule 1 - Bug] DELETE 204 quebrava a criação do app.** A rota `DELETE /{id}` (status 204) com retorno `-> None` fazia o FastAPI inferir `response_model` e disparar `AssertionError: Status code 204 must not have a response body` na construção do app (23 testes em erro). Fix: `response_model=None` explícito na rota. Encontrado na Task 2; corrigido no mesmo commit (cb56f50).

## Tech debt
- Herdada TD-017 (SPATIAL INDEX nullable — Plan 01).
- SUG: completar o guard de "entregas ativas" em `remove_neighborhood` contra a tabela `deliveries` na Phase 7 (hoje usa cobertura/preço como proxy).

## Verificação local
- `uv run pytest -m "not mysql"` → **196 passed, 10 skipped, 7 deselected**.
- `uv run pytest tests/neighborhoods/test_models.py` → 7 passed (CRUD, area-scope 404, archive, polígono inválido).
- `uv run ruff check app/neighborhoods app/api/v1/router.py` + `format` → limpos.
- `uv run basedpyright app/neighborhoods` → 0 errors.

## Itens @pytest.mark.mysql (rodar ao vivo)
- `tests/neighborhoods/test_spatial.py` — `point_in_polygon` (ST_Contains) ponto dentro/fora. Comando: `uv run pytest -m mysql tests/neighborhoods/test_spatial.py`.
- Persistência de polígono via `ST_GeomFromGeoJSON` + leitura `ST_AsGeoJSON` só existem em MySQL real.

## Self-Check: PASSED
- spatial.py, service.py, router.py — FOUND. Commits 964ab8d, cb56f50 — FOUND.
