---
phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
plan: 01
subsystem: backend (areas + migration + test scaffold)
tags: [spatial, migration, area-config, audit, tdd-scaffold]
requires:
  - "Phase 5 couriers/audit/AreaScoped (entidades + write_audit)"
provides:
  - "migration 0005 (neighborhoods_catalog + courier_coverage_areas + courier_pricing_tables + couriers.is_online/max_concurrent)"
  - "AreaConfig Pydantic tipada (ranges) + SENSITIVE_KEYS + diff_sensitive"
  - "update_area validado/auditado (retorna diff sensivel)"
  - "Wave 0 test scaffold de toda a Phase 6"
affects:
  - "apps/api/app/areas/* (service.update_area muda assinatura: retorna tupla)"
tech-stack:
  added: []
  patterns:
    - "coluna espacial POLYGON via DDL bruto MySQL-only (Pitfall 3)"
    - "config tipada substituindo JSON cru + audit before/after (Pitfall 4)"
key-files:
  created:
    - apps/api/alembic/versions/0005_area_operable.py
    - apps/api/app/areas/config_schema.py
    - apps/api/tests/neighborhoods/__init__.py
    - apps/api/tests/neighborhoods/conftest.py
    - apps/api/tests/neighborhoods/test_models.py
    - apps/api/tests/neighborhoods/test_spatial.py
    - apps/api/tests/couriers/test_coverage.py
    - apps/api/tests/couriers/test_pricing_floor.py
    - apps/api/tests/couriers/test_availability.py
    - apps/api/tests/areas/__init__.py
    - apps/api/tests/areas/test_config_audit.py
  modified:
    - apps/api/app/areas/service.py
    - apps/api/app/areas/router.py
decisions:
  - "update_area retorna (Area, diff_sensivel) — router grava area.config.update so quando diff != None"
  - "AreaUpdate.config permanece dict (validado no service via AreaConfig) — 422 RFC-7807 fora do range"
  - "sem SPATIAL INDEX em polygon nullable (TD-017)"
metrics:
  duration: ~30min
  tasks: 3
  files: 13
  completed: 2026-06-10
---

# Phase 6 Plan 01: Fundação backend (migration 0005 + AreaConfig + scaffold) Summary

Migration 0005 cria o schema espacial/relacional da Phase 6 (3 tabelas + 2 colunas em couriers) reusando as convenções de 0004; `AreaConfig` Pydantic v2 (`extra="forbid"`, ranges) substitui o JSON cru de `Area.config` com audit `before/after` em mudança sensível (RN-012); e o Wave 0 test scaffold de toda a fase está criado (importorskip protege módulos das Plans 02/03 ainda inexistentes).

## Tasks Completed

| Task | Nome | Commit | Arquivos-chave |
|------|------|--------|----------------|
| 1 | Wave 0 test scaffold | 07da40c | tests/neighborhoods/*, tests/couriers/test_{coverage,pricing_floor,availability}.py, tests/areas/test_config_audit.py |
| 2 | Migration 0005 (schema espacial+relacional) | f98b435 | alembic/versions/0005_area_operable.py |
| 3 | AreaConfig tipada + audit sensível | 47971af | app/areas/config_schema.py, service.py, router.py |

## Decisões

- **`update_area` muda de assinatura** para `(Area, diff_sensivel)`. Único caller fora dos testes é o router de areas (atualizado). O router grava `write_audit("area.config.update", before/after)` só quando o diff sensível não é None (name-only → sem audit de config).
- **Polígono via DDL bruto MySQL-only** (`ALTER TABLE ... ADD COLUMN polygon POLYGON NULL SRID 4326` no branch `is_mysql`); SQLite (`create_all`) nunca vê o tipo nativo (Pitfall 3). A coluna é manipulada só via `func.ST_*` na Plan 02 (sem GeoAlchemy2 — LOW-1).
- **Sem SPATIAL INDEX em `polygon`** (nullable — Pitfall 1/LOW-4) → TD-017 registrada (post_launch_quarter).

## Deviations from Plan

Nenhum desvio de comportamento. Ajuste menor: `AreaUpdate.config` foi mantido como `dict | None` (validado no service via `AreaConfig`) em vez de tipar o campo Pydantic diretamente como `AreaConfig | None` — o resultado de validação (422 fora do range) e a mensagem RFC-7807 são equivalentes, e o service centraliza o parse + diff. Sem impacto no contrato externo.

## Tech debt
- **TD-017** (novo, post_launch_quarter): `neighborhoods_catalog.polygon` sem SPATIAL INDEX (coluna nullable).
- **TD-018** (pré-registrada para Plan 03, post_launch_quarter): aumento de piso retroativo só sinaliza.
- TD-010 (existente): aware-UTC garantido por `write_audit`.

## Verificação local
- `uv run pytest -m "not mysql"` → **189 passed, 13 skipped (importorskip scaffold), 7 deselected (mysql)**.
- `uv run pytest tests/areas/test_config_audit.py` → 10 passed.
- `uv run ruff check app/areas tests/areas` + `ruff format --check` → limpos.
- `uv run basedpyright app/areas` → 0 errors.
- `uv run python -c "ast.parse(...0005...)"` + `uv run alembic upgrade head --sql` → parse + offline SQL OK (POLYGON DDL presente no branch MySQL).

## Itens @pytest.mark.mysql (rodar ao vivo)
- `tests/neighborhoods/test_spatial.py` (ST_Contains ponto dentro/fora) — `uv run pytest -m mysql tests/neighborhoods/test_spatial.py` (ponto-em-polígono real chega com a Plan 02).
- Migration 0005 reversível em MySQL real — `uv run alembic upgrade head && uv run alembic downgrade -1`.

## Self-Check: PASSED
- Arquivos criados: 0005_area_operable.py, config_schema.py, test_spatial.py, test_config_audit.py — todos FOUND.
- Commits 07da40c, f98b435, 47971af — todos FOUND.
