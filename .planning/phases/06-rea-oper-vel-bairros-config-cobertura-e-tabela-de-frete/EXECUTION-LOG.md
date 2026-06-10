# EXECUTION-LOG — Phase 6: Área operável (bairros, config, cobertura e tabela de frete)

> Executor único (sequencial por wave, apesar do parallel-hint back-front). Backend
> primeiro (Waves 1–2, contrato fixado), depois frontend (Wave 3). Commit atômico
> por task. Espacial via `func.ST_*` nativo (sem GeoAlchemy2 — LOW-1); testes
> espaciais `@pytest.mark.mysql` (rodam ao vivo). Stubs/SQLite em CI.

**Início:** 2026-06-10T~21:50Z · **Fim:** 2026-06-10T~22:10Z

## Baseline antes da Phase 6
- Backend: 179 passed (not-mysql), 5 deselected (mysql). Frontend: 46 testes. Árvore limpa em `master`.

## Wave 1 — fundação backend (Plan 06-01)

| Task | Descrição | Commit | Resultado |
|------|-----------|--------|-----------|
| 1 | Wave 0 test scaffold (neighborhoods/couriers/areas config audit) | `07da40c` | 15 testes coletáveis (importorskip protege módulos das Plans 02/03); marker mysql já registrado |
| 2 | Migration 0005 — schema espacial + cobertura/preço + couriers online | `f98b435` | parse + `alembic upgrade head --sql` OK; POLYGON DDL MySQL-only; sem SPATIAL INDEX nullable (TD-017) |
| 3 | AreaConfig tipada (ranges) + audit em config sensível | `47971af` | test_config_audit 10 passed; 422 fora do range; before/after sensível |

## Wave 2 — backend espacial + oferta (Plans 06-02, 06-03)

| Task | Descrição | Commit | Resultado |
|------|-----------|--------|-----------|
| 02-1 | neighborhoods models/schemas + spatial (func.ST_*, lat-first) | `964ab8d` | validate_polygon_geojson (shapely anti-DoS); point_in_polygon ST_Contains; shapely adicionado |
| 02-2 | neighborhoods service CRUD area-scoped + router /v1/neighborhoods | `cb56f50` | CRUD cross-area 404; remoção bloqueada cita o bairro; **[Rule 1] DELETE 204 response_model=None** |
| 03-1 | cobertura (RN-003) + tabela de frete com piso (RN-015) | `0cae675` | is_eligible dois pontos+exclusão; assert_above_floor cita o piso; 2 modelos novos |
| 03-2 | disponibilidade online/offline (REQ-018) + rotas self-only | `2039232` | só active online (409); compute_busy derivado; **[Rule 2] self-only por user_id (sem role 'courier' fantasma)** |
| — | ruff format dos testes | `f7d5e86` | line-length |

## Wave 3 — frontend (Plans 06-04 admin, 06-05 entregador)

| Task | Descrição | Commit | Resultado |
|------|-----------|--------|-----------|
| 04-1 | jx-data-table — primitivo de tabela governado | `b69912b` | header sticky + aria-sort + 4 estados; spec 5 verde; zero hex |
| 04-2 | tela 21A config da área (máscara monetária + confirmação sensível) | `35b1d61` | ranges no blur; diff before→after; rotas /admin/config e /admin/bairros |
| 04-3 | tela 21B catálogo de bairros (CRUD sobre jx-data-table) | `ad0967f` | GeoJSON validado client (UX); remoção bloqueada role=alert; SUG-009 |
| 05-1 | tela 10 entregador cobertura + preços (validação de piso) | `e902352` | modo bairro/km; piso citado role=alert; jx-coverage-list; safe-area |
| 05-2 | jx-availability-toggle online/offline (só active) | `5848a36` | role=switch + aria-live; não-active warn-banner; revert() para 409 |

## Resultado final
- **Backend:** ruff check limpo, ruff format limpo (151 arquivos), basedpyright **0 errors**, **206 passed** (not-mysql), 7 deselected (mysql).
- **Frontend:** `ng build` OK (**bundle initial 598.40 KB / 160.96 KB gzip** < 400 KB de main), `ng lint` All files pass, **65 testes** verdes, **0 #hex** (Gate 2).

## Desvios (deviation rules)
- **[Rule 1 - Bug]** `DELETE /neighborhoods/{id}` (204) com retorno `-> None` fazia o FastAPI inferir response_model e quebrar a criação do app (`AssertionError: Status code 204 must not have a response body`). Fix: `response_model=None`. (commit cb56f50)
- **[Rule 2 - Segurança]** Rotas do entregador (coverage/pricing/availability) usam self-only por `Courier.user_id == token.user` + area scope (cross → 404), em vez do `require_role("courier")` literal do plano — o role "courier" não existe no `resolve_role` do projeto. (commit 2039232)

## Pendente ao vivo (MySQL real + smoke visual)
- `cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` (migration 0005 reversível).
- `cd apps/api && uv run pytest -m mysql tests/neighborhoods/test_spatial.py` (ST_Contains ponto dentro/fora — REQ-003, critério de aceite do ROADMAP).
- Smoke visual telas 21A/21B/10 (claro+dark; validação de piso citando o valor; axe sem violações críticas).
