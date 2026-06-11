# EXECUTION-LOG — Phase 9: Execução, comprovação, tracking público e notificações

> Executor único, sequencial (backend → frontend → testes/jobs). Commit atômico por task em master.
> Início: 2026-06-11T01:13Z · 19 tasks (T-01..T-19) em 7 waves.

## Resultado por wave

### Wave 0 — spikes/fundação
| Task | Descrição | Commit |
|------|-----------|--------|
| T-19 | TD-019 (tiles OSM prod) + TD-020 (background polling) | `f952df5` |
| T-01 | Spike A3 — contrato da foto (EXIF + GPS client) | `d0e9678` |
| T-02 | Geofence `ST_Distance_Sphere` + haversine fallback | `fad3252` |

### Wave 1 — backend núcleo
| Task | Descrição | Commit |
|------|-----------|--------|
| T-03 | Pipeline comprovação foto+EXIF/GPS (o oposto do KYC) | `111815f` |
| T-05 | Endpoint público de tracking + serializer minimização PII | `04e423d` |
| T-06 | Ingestão de localização (anti-IDOR) + delivery_locations | `8276780` |

### Wave 2 — backend orquestração
| Task | Descrição | Commit |
|------|-----------|--------|
| T-04 | Transições F-06 + reveal RN-013 + custo cancelamento RN-004 | `f9cad54` |
| T-09 | Notificações multicanal + push_subscriptions + confirmação direta | `ce0c51c` |
| T-10 | Número de referência (E4) + liberação manual | `d387d9e` |

### Wave 3 — jobs + migration + front service
| Task | Descrição | Commit |
|------|-----------|--------|
| T-07 | Jobs arq (finalize 24h / purge 24h / absent 10min) | `a915b05` |
| T-11 | Migration 0008 reversível + 8 componentes UI base | `16a3e7b` |
| T-08 | Polling de localização resiliente + offline (A5) | `57f2f67` |

### Waves 4-6 — UI
| Task | Descrição | Commit |
|------|-----------|--------|
| T-16 | Tela 26 (tracking público) + jx-live-map lazy + dark | `61fd8d0` |
| T-12/13/14/15/17 | Telas 07/13 + offline + opt-in push + timeline/banner | `fece7c9` |
| T-18 | Visual regression baselines (8 componentes) | `cefc499` |

## Gate 7 (verificação local)

**Backend (`apps/api`):**
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 248 files already formatted
- `uv run basedpyright` (scope app+tools) → 0 errors, 0 warnings
- `uv run pytest -m "not mysql"` → **326 passed, 16 deselected** (baseline 265 → +61)
- piexif adicionado como dev-dep (gera JPEG com GPS nos testes; produção lê EXIF com Pillow)

**Frontend (`apps/web`):**
- `npx ng build` → **Initial total 162.88 kB** (budget 400 kB); chunk `maplibre-gl` 231 kB transfer **LAZY** (fora do main); `public-tracking-page` 2.73 kB
- `npm run lint` → All files pass linting
- `ng test` → **121 SUCCESS** (baseline 80 → +41)
- `grep -rE "#E84E1B|#FAF6EE" apps/web/src --include="*.scss" | grep -v _tokens.scss` → **0**

## Pendente ao vivo (MySQL real — `pytest -m mysql`)

```
cd apps/api
# geofence ST_Distance_Sphere ponto dentro/fora + SRID/eixo/unidade:
uv run pytest -m mysql tests/proofs/test_geofence_db.py
# migration 0008 reversível (upgrade -> downgrade -1 -> upgrade head):
uv run pytest -m mysql tests/db/test_migration_0008.py
```

Fixtures @mysql alinhadas a `settings.database_url` + NullPool + dispose-no-loop (lição Phase 7 — NÃO TEST_MYSQL_URL hardcoded).

## Desvios (deviation rules)

- **Rule 3 (estrutura real do frontend):** o PLAN listava paths `apps/web/src/app/...`; a estrutura real é `apps/web/src/{features,shared,core}`. Componentes criados em `shared/components/`, telas em `features/`. Rotas em `app/app.routes.ts`.
- **Rule 2 (coluna cancel_cost_cents):** RN-004 exige registrar o custo na entrega; adicionada coluna `deliveries.cancel_cost_cents` (na migration 0008) — não estava explícita no schema.
- **Rule 3 (piexif dev-dep):** necessário para gerar JPEG com EXIF GPS nos testes (produção usa Pillow).
- **Rule 1 (FastAPI 204 + response):** endpoints 204 (locations, push-subscriptions DELETE) precisavam retornar `Response(status_code=204)` explícito (FastAPI rejeita body em 204 com response_model implícito).
- **Rule 3 (`attributionControl: true`):** removido (typing MapLibre v5 não aceita boolean; atribuição é default).
