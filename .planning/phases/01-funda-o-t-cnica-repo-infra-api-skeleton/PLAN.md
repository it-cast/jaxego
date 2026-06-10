---
phase: 01-funda-o-t-cnica-repo-infra-api-skeleton
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .python-version
  - pyproject.toml
  - uv.lock
  - .gitignore
  - .env.example
  - README.md
  - apps/api/app/__init__.py
  - apps/api/app/main.py
  - apps/api/app/core/config.py
  - apps/api/app/core/logging.py
  - apps/api/app/core/observability.py
  - apps/api/app/core/exceptions.py
  - apps/api/app/middleware/__init__.py
  - apps/api/app/middleware/request_context.py
  - apps/api/app/api/__init__.py
  - apps/api/app/api/v1/__init__.py
  - apps/api/app/api/v1/router.py
  - apps/api/app/api/v1/health.py
  - apps/api/app/db/__init__.py
  - apps/api/app/db/base.py
  - apps/api/app/db/session.py
  - apps/api/app/workers/__init__.py
  - apps/api/app/workers/settings.py
  - apps/api/alembic.ini
  - apps/api/alembic/env.py
  - apps/api/alembic/script.py.mako
  - apps/api/alembic/versions/0001_baseline.py
  - apps/api/Dockerfile
  - infra/docker-compose.yml
  - infra/nginx/jaxego.conf
  - apps/api/tests/conftest.py
  - apps/api/tests/test_health.py
  - apps/api/tests/test_naive_datetime_guard.py
  - apps/api/tools/check_naive_datetime.py
  - .github/workflows/ci.yml
autonomous: false
requirements: [REQ-052, REQ-050, REQ-022]
must_haves:
  truths:
    - "Desenvolvedor sobe a stack completa com um comando e a API responde em /health"
    - "GET /health retorna 200 com status de MySQL e Redis"
    - "Todo log é JSON estruturado em stdout com request_id e campos obrigatórios; nenhuma PII"
    - "Sentry inicializa só quando SENTRY_DSN está presente (no-op em dev)"
    - "Alembic está configurado e a migration baseline aplica/reverte sem tabelas de domínio"
    - "Pipeline GitHub Actions roda ruff + basedpyright + pytest e fica verde"
    - "Naive datetime em código de domínio é rejeitado por teste/lint custom"
  artifacts:
    - path: "pyproject.toml"
      provides: "Deps travadas (FastAPI 0.115, SQLAlchemy 2.x, Alembic, arq, ruff, basedpyright, pytest) + config das ferramentas"
      contains: "fastapi"
    - path: "apps/api/app/main.py"
      provides: "App factory create_app() com middleware, router /v1 e Sentry condicional"
      contains: "def create_app"
    - path: "apps/api/app/api/v1/health.py"
      provides: "Endpoint GET /health (raiz, sem prefixo /v1) com checagem de MySQL e Redis"
      contains: "health"
    - path: "apps/api/app/middleware/request_context.py"
      provides: "Middleware de request_id + duração + log estruturado da request"
      contains: "request_id"
    - path: "apps/api/alembic/versions/0001_baseline.py"
      provides: "Migration baseline vazia (sem tabelas de domínio)"
      contains: "def upgrade"
    - path: "infra/docker-compose.yml"
      provides: "Serviços api, worker, mysql:8.0, redis com healthchecks e volume nomeado"
      contains: "mysql:8.0"
    - path: ".github/workflows/ci.yml"
      provides: "Pipeline CI: lint (ruff) + typecheck (basedpyright) + test (pytest)"
      contains: "basedpyright"
    - path: "apps/api/tools/check_naive_datetime.py"
      provides: "Guard custom proibindo naive datetime em código de domínio (TD-010)"
      contains: "tzinfo"
  key_links:
    - from: "apps/api/app/main.py"
      to: "apps/api/app/middleware/request_context.py"
      via: "app.add_middleware no create_app"
      pattern: "add_middleware.*RequestContext"
    - from: "apps/api/app/api/v1/health.py"
      to: "MySQL + Redis"
      via: "SELECT 1 via engine async + redis.ping()"
      pattern: "ping|SELECT 1"
    - from: ".github/workflows/ci.yml"
      to: "apps/api/tools/check_naive_datetime.py"
      via: "step do job que roda o guard via pytest"
      pattern: "pytest"
---

# PLAN — Phase 1 Plan 01-01: Fundação técnica (repo, infra, API skeleton)

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Entregar a fundação técnica do monorepo Jaxegô: backend FastAPI mínimo com `GET /health`, Docker Compose (api, worker arq, mysql 8.0, redis), Alembic configurado com migration baseline vazia, observabilidade base (logs JSON + request_id + Sentry condicional) e pipeline GitHub Actions verde (ruff + basedpyright + pytest), incluindo o guard de naive datetime desde o commit 1. **Sem** regra de negócio, entidade de domínio, auth ou UI.

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] `docker compose -f infra/docker-compose.yml up -d && curl -f localhost:8000/health` → exit 0 (status 200, com MySQL e Redis `ok`)
- [ ] `uv run pytest` (a partir de `apps/api/`) → exit 0
- [ ] `uv run ruff check .` e `uv run ruff format --check .` → exit 0
- [ ] `uv run basedpyright` → exit 0 (sem erro de tipo)
- [ ] `uv run alembic upgrade head` aplica e `uv run alembic downgrade base` reverte a baseline sem erro
- [ ] Logs da request `/health` saem em JSON em stdout com `request_id`, `endpoint`, `method`, `status_code`, `duration_ms`; nenhum campo PII
- [ ] Subir a API sem `SENTRY_DSN` não quebra (Sentry no-op); com DSN fake, init não falha
- [ ] Teste `test_naive_datetime_guard.py` rejeita `datetime.now()`/`.replace(tzinfo=None)` em código de domínio (TD-010)
- [ ] Pipeline GitHub Actions verde no commit inicial (jobs lint, typecheck, test)
- [ ] `uv.lock` versionado; `uv sync --frozen` sem divergência
- [ ] Commit atômico por wave com mensagem padronizada (`feat(phase-1/...)`)

## REQs referenciados

- REQ-052 — Infra Docker Compose + CI/CD (compose sobe api/worker/redis/mysql; GitHub Actions lint → testes)
- REQ-050 (base) — Observabilidade: logs estruturados stdout, `request_id` em todo log, campos obrigatórios do `config.json`, Sentry wired
- REQ-022 (fundação) — Migrations Alembic + convenções de schema (utf8mb4, UTC, naming convention de constraints); nenhuma tabela de domínio nesta phase

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a uma ou mais tasks deste plano.

- `meta/orchestration-decision-tree` — T-01, T-08: protocolo de leitura obrigatória (CLAUDE.md → STATE.md → git log) seguido antes de planejar; enriquecimento automático de skills por domínio aplicado — domínio "deploy/docker" injeta `docker-production-ready` (T-04), "nova tabela/alembic" injeta `mysql-schema-design` (T-03), garantindo que cada task carregue a skill de domínio correta.
- `quality/observability-production` — T-02, T-05: middleware de `request_id` + timing exatamente como o padrão `RequestContextMiddleware` da skill (bind de contextvars + log `request_completed` com `duration_ms` e header `X-Request-ID`); campos obrigatórios do log batem com `config.json > observability.required_log_fields` (request_id, user_id, endpoint, method, status_code, duration_ms); PII proibida segue `pii_fields_forbidden_in_logs`; Sentry init condicional por DSN; `/health` como health endpoint do "pilar uptime".
- `domain/fastapi-production-patterns` — T-01, T-02, T-05: estrutura canônica `app/{core,api/v1,db,workers,middleware}`, `create_app()` factory sem lógica, router magro, `pythonpath = ["src"]`/`apps/api` no pyproject (regra inegociável que evita "0 testes coletados"), hierarquia `AppError` + handler global, schemas Pydantic v2 com `ConfigDict(from_attributes=True)` para o payload do health.
- `domain/docker-production-ready` — T-04: Dockerfile multi-stage com `uv sync --frozen --no-dev`, usuário não-root (`USER app`), `HEALTHCHECK` batendo em `/health`, `EXPOSE 8000`; compose com healthcheck por serviço, volume nomeado para MySQL, `--workers 1` em dev.
- `domain/mysql-schema-design` — T-03: `MetaData` com `naming_convention` canônica (ix/uq/ck/fk/pk), charset `utf8mb4`/collation no `__table_args__` da Base, `DATETIME(6)` UTC como padrão de timestamp; engine SQLAlchemy 2.x async (`aiomysql`); Alembic configurado mas **sem** tabela de domínio (baseline vazia, REQ-022).
- `domain/github-actions-ci` — T-08: pipeline canônico com `astral-sh/setup-uv@v5` + `uv sync --frozen` (divergência de lockfile = erro), MySQL 8.0 real como service para integração, `alembic upgrade head` no CI pega migration quebrada, `concurrency` + `cancel-in-progress`; jobs `lint` (ruff), `typecheck` (basedpyright), `test` (pytest).
- `product/api-design-contracts` — T-02, T-05: contrato de resposta padronizado do health endpoint (`{ status, db, redis, version }`), envelope de erro RFC-7807-like (`{ error: { code, message, request_id } }`) consistente em toda a API, versionamento por prefixo `/v1` para endpoints de domínio (DRV-003) — com o health/readiness probe deliberadamente fora do prefixo em `/health` (raiz). Dispara por feature:api_endpoint + path **/api/** + keyword "endpoint"/"GET /".
- `quality/senior-quality-bar` — T-01/T-06: "segredo no repo" = FAIL-BLOCK respeitado (`.env` no `.gitignore`, `.env.example` sem valores reais, DSN/credenciais só via env, nunca commitados); T-03/T-05: sem N+1 (health usa `SELECT 1` + `redis.ping()`, zero query de domínio); sem PII em log (campos proibidos do `config.json` jamais logados). Dispara por phase_type:code (Gate 8 — toda phase com código) + recommended_for:has_api.

## Skills Dispensadas (com justificativa)

- `ui-ux-pro-max`, `quality/accessibility-pro`, `product/component-library-governance`, `ux-advanced/design-tokens-system`, `ux-advanced/empty-states-polish`, `ux-advanced/dark-mode-theming`, `quality/error-ux-patterns`, `ux-advanced/form-ux-mastery`, `ux-advanced/responsive-breakpoint-strategy` e toda a `sprint_ui_matrix` — `has_ui: false` nesta phase (ROADMAP); não há nenhuma tela. Entram a partir da Phase 3.
- `br/ux-copywriting-ptbr`, `br/brazilian-forms` — sem copy de usuário final nem formulário brasileiro nesta fundação (só infra/backend). Phases 4+.
- `owasp-security` — auth, PII e endpoints de domínio são escopo da Phase 2 (`has_pii: false` aqui). Aplicada **de leve** apenas como baseline de config de segredos: `.env` no `.gitignore`, `.env.example` sem valores reais, segredos só via env (nunca commitados), regra "secret no repo" do Senior Quality Bar respeitada (T-01/T-06). Threat model completo é dispensado (ver seção Threat model).
- `domain/monorepo-deploy-safety` — invariantes de deploy-safety (versionamento de artefatos, rollback seguro, ordem de migração no deploy, blue/green) são conhecidas e relevantes, mas o deploy real é escopo da Phase 14. Nesta fundação apenas se **estabelece a estrutura do monorepo** (`apps/api/`, `infra/`, `.github/workflows/`) sem pipeline de deploy ativo — o `ci.yml` cobre lint/typecheck/test, com build/deploy por tag deixado como esqueleto comentado. Sem deploy ativo nesta phase, não há invariante de deploy-safety a aplicar agora; a skill será 🔒 obrigatória na Phase 14.
- `domain/safe2pay-escrow-br`, `domain/saas-billing-canonical` — sem billing/pagamento nesta phase (Phases 10+).
- `mobile/*`, `ux-advanced/gesture-touch-patterns` — `mobile: false`. Phase 3+.
- `domain/llm-integration-patterns` — infra de LLM é Phase 14 (TD-008, `has_ai: false`).

---

## Tech debt deste plano (verificação obrigatória v0.8+)

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime (lição auditada v1.0) — `urgency_class: pre_launch_high`, prazo "toda phase com timestamps" | Entra: a fundação cria o ponto de vigilância. O guard precisa existir desde o commit 1 para todas as phases seguintes (2, 7, 9, 10, 11) herdarem. | T-07 (guard custom) + T-03 (`DATETIME(6)` UTC, `timezone.utc` na borda) |
| TD-013 | Taxas sem versionamento temporal (`effective_from/until`) — `pre_launch_medium`, "Phase 10 decide" | Deferido: sem tabelas de domínio nesta phase; decisão de schema é da Phase 10. Sem ação aqui. | — |
| TD-001 | Sharding não implementado — `wont_fix_documented` | Deferido: gatilho >50 áreas; multi-área lógico em 1 MySQL é exatamente o desenhado. | — |

Demais TDs (002–009, 011, 012) têm prazo/gatilho fora desta phase ou são pós-M1.

---

## Open questions / LOW confidence do RESEARCH

`N/A — esta phase não passou por `/gsd:research-phase` (foundation/Discovery Level 0–1: stack 100% travada por ADR-002, sem opções a escolher). Todas as decisões já estão fixadas em CONTEXT.md (D-01..D-10) e DECISIONS.md (ADR-002, DRV-002, DRV-003). Nada marcado como LOW confidence.

---

## Threat model

`N/A — este plano não toca autenticação, PII nem endpoint de domínio (`has_pii: false`, auth é Phase 2).` Avaliado e dispensado conscientemente. Baseline mínimo de segredos aplicado mesmo assim (ver `owasp-security` em Skills Dispensadas): `.env` ignorado, `.env.example` sem segredos reais, nenhuma credencial no repo (Senior Quality Bar: "segredo no repo" = FAIL-BLOCK).

---

## Performance budget (há endpoint `/health`)

Herdado de `.planning/config.json > performance_budget` e `stack.md:55`.

**Backend:**
- p95 de latência ≤ 200 ms nos endpoints quentes (orçamento do projeto). `/health` é leve mas exerce o caminho de middleware + checagem de MySQL/Redis — a fundação **não pode introduzir overhead estrutural** que comprometa o budget das phases seguintes.
- p99 ≤ 400 ms para `/health`.
- N+1 queries: zero (não há query de domínio; health usa `SELECT 1` + `redis.ping()`).
- Connection pooling: engine async configurado com `pool_size`/`max_overflow` razoáveis (default sensato) — dimensionado para não estrangular sob carga futura.
- Middleware de observability deve ser O(1) por request (bind de contextvars + um log); nada de I/O bloqueante no caminho quente.

**Frontend:** `N/A — sem UI nesta phase.`

Ferramenta de medição:
- Backend: assertion leve no teste de `/health` (responde rápido); Prometheus/medição real de p95 valida na Phase 14 sob carga sintética (REQ-050 completo).

---

## Observability checklist (há endpoint + worker)

Aplicando skill `observability-production` + `config.json > observability`:

- [ ] `/health` loga: `request_id`, `user_id` (null nesta phase, campo presente), `endpoint`, `method`, `status_code`, `duration_ms` (campos obrigatórios do config)
- [ ] Erros 4xx logados como WARNING; 5xx como ERROR (handler global de `AppError`)
- [ ] Queries > `slow_query_threshold_ms` (100ms) logadas com WARNING (hook de engine preparado, ainda sem queries de domínio)
- [ ] Zero PII em logs — nenhum dos campos `cpf, cnpj, email, password, token, jwt, card_number, cvv` aparece em log (guard de config respeitado por design; não há esses campos nesta phase)
- [ ] `request_id` aceito via header `X-Request-ID` ou gerado (uuid4) e devolvido no response header
- [ ] Sentry inicializado condicionalmente por `SENTRY_DSN` (no-op sem DSN); `environment` e `release` setados; PII scrubbing default ligado
- [ ] `/health` é o health endpoint do serviço (consumido pelo HEALTHCHECK do Docker e pelo CI)

---

## Error UX checklist

`N/A — este plano é backend/infra, sem UI de erro.` Erros do `/health` seguem o formato RFC-7807-like de `fastapi-production-patterns` (`{ "error": { "code", "message", "request_id" } }`) para o frontend das phases futuras consumir.

---

## Integration contracts

`N/A — `integration_check: false` no ROADMAP para esta phase; é single-layer (backend/infra, sem cliente consumidor cross-layer).` Avaliado e dispensado.

---

## Tasks

Formato estruturado — cada task tem skills aplicadas e critério de sucesso isolado.

### T-01 — Monorepo + uv + pyproject + config de ferramentas

- **Type:** infra
- **Files:** `.python-version`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example`, `README.md`, `apps/api/app/__init__.py`, `apps/api/app/core/config.py`
- **Skills aplicadas:**
  - `meta/orchestration-decision-tree` — leitura obrigatória feita; estrutura `apps/api/` conforme D-01.
  - `domain/fastapi-production-patterns` — `pythonpath`/rootdir apontando para `apps/api` no `[tool.pytest.ini_options]` (regra inegociável: sem isso pytest coleta 0 testes); `core/config.py` como única fonte de env via `pydantic-settings`.
  - `owasp-security` (leve) — `.env` no `.gitignore`, `.env.example` sem segredos reais, segredos só por env.
  - `quality/senior-quality-bar` — "segredo no repo" = FAIL-BLOCK: garante `.env` ignorado e `.env.example` apenas com placeholders.
- **Descrição:** Cria o monorepo (D-01: `apps/api/`, `infra/`, `.github/workflows/`). `.python-version` pinado em `3.13` (D-02, ADR-002 — sistema tem 3.12, `uv` instala/usa 3.13). `pyproject.toml` com deps travadas: `fastapi==0.115.*`, `sqlalchemy>=2,<3`, `alembic`, `aiomysql`, `redis`, `arq`, `pydantic-settings`, `structlog`, `sentry-sdk`; dev: `ruff`, `basedpyright`, `pytest`, `pytest-asyncio`, `httpx`. Configura `[tool.ruff]`, `[tool.basedpyright]`, `[tool.pytest.ini_options]`. Gera e versiona `uv.lock`. `core/config.py` define `Settings` (DATABASE_URL, REDIS_URL, SENTRY_DSN opcional, ENVIRONMENT). `.env.example` com placeholders.
- **Success:** `uv sync --frozen` instala 3.13 sem divergência; `uv run python -c "from app.core.config import Settings; Settings()"` carrega config; `uv run ruff check .` roda (mesmo que vazio); `.env` ignorado pelo git.
- **Estimate:** ~1.5h
- **Depends on:** none

### T-02 — App factory + middleware de observabilidade + Sentry condicional

- **Type:** new_endpoint (skeleton)
- **Files:** `apps/api/app/main.py`, `apps/api/app/core/logging.py`, `apps/api/app/core/observability.py`, `apps/api/app/core/exceptions.py`, `apps/api/app/middleware/__init__.py`, `apps/api/app/middleware/request_context.py`, `apps/api/app/api/__init__.py`, `apps/api/app/api/v1/__init__.py`, `apps/api/app/api/v1/router.py`
- **Skills aplicadas:**
  - `domain/fastapi-production-patterns` — `create_app()` factory sem lógica; router magro; hierarquia `AppError` + handler global que devolve `{ "error": { code, message, request_id } }`.
  - `quality/observability-production` — `RequestContextMiddleware` (bind de `request_id`, `endpoint`, `method` em contextvars; log `request_completed` com `status_code` + `duration_ms`; header `X-Request-ID` no response); structlog configurado para JSON em stdout; Sentry init condicional por `SENTRY_DSN` (no-op sem DSN).
  - `product/api-design-contracts` — contrato de erro RFC-7807-like (`{ error: { code, message, request_id } }`) padronizado para toda a API; router de domínio versionado por prefixo `/v1` (DRV-003), com o health probe fora do prefixo (montado na raiz, ver T-05).
- **Descrição:** `main.py` expõe `create_app()` que: configura logging JSON (T via `core/logging.py`), inicializa Sentry condicional (`core/observability.py` — só se `settings.SENTRY_DSN`), adiciona `RequestContextMiddleware`, registra handler global de `AppError`, inclui `api/v1/router.py` (prefixo `/v1`) e monta o router de health na raiz (sem prefixo). `app = create_app()` no final para o uvicorn/Docker. Campos de log obrigatórios = `config.json > required_log_fields`; `user_id` presente como `None` nesta phase. Endpoints de domínio são versionados por prefixo `/v1` (DRV-003); o health/readiness probe fica em `/health` (raiz, convenção Docker/Nginx/k8s).
- **Success:** `uv run uvicorn app.main:app` sobe; request a qualquer rota emite log JSON em stdout com os 6 campos obrigatórios + `X-Request-ID` no response; sem `SENTRY_DSN` não quebra; com DSN fake, init não levanta exceção.
- **Estimate:** ~2h
- **Depends on:** T-01

### T-03 — SQLAlchemy 2.x async + Base/metadata + Alembic + migration baseline

- **Type:** migration
- **Files:** `apps/api/app/db/__init__.py`, `apps/api/app/db/base.py`, `apps/api/app/db/session.py`, `apps/api/alembic.ini`, `apps/api/alembic/env.py`, `apps/api/alembic/script.py.mako`, `apps/api/alembic/versions/0001_baseline.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — `MetaData(naming_convention=...)` canônica (ix/uq/ck/fk/pk); `Base` com `__table_args__` charset `utf8mb4`/collation `utf8mb4_unicode_ci`; padrão `DATETIME(6)` UTC para timestamps (DRV-002).
  - `domain/fastapi-production-patterns` — `db/session.py` com `create_async_engine` (aiomysql) + `async_sessionmaker`; sem lógica de domínio.
  - `quality/senior-quality-bar` — sem N+1 por design (zero query de domínio nesta phase; engine async com pooling razoável evita gargalo estrutural futuro).
- **Descrição:** `db/base.py` define `Base(DeclarativeBase)` com `metadata` (naming convention + utf8mb4). `db/session.py` cria engine async a partir de `settings.DATABASE_URL` (`mysql+aiomysql://`) + `async_sessionmaker`. Alembic configurado (`env.py` async, lê `target_metadata = Base.metadata`, URL via env). Migration `0001_baseline.py` é **vazia** (sem tabela de domínio — REQ-022, D-04): apenas garante baseline aplicável/reversível e estabelece convenções. Timestamps UTC sempre; conversão só na borda (TD-010).
- **Success:** `uv run alembic upgrade head` aplica baseline contra MySQL; `uv run alembic downgrade base` reverte sem erro; `Base.metadata` importável com naming convention ativa; nenhuma tabela de domínio criada.
- **Estimate:** ~2h
- **Depends on:** T-01

### T-04 — Worker arq + Docker Compose (api, worker, mysql 8.0, redis) + Nginx documentado

- **Type:** infra
- **Files:** `apps/api/app/workers/__init__.py`, `apps/api/app/workers/settings.py`, `apps/api/Dockerfile`, `infra/docker-compose.yml`, `infra/nginx/jaxego.conf`
- **Skills aplicadas:**
  - `domain/docker-production-ready` — Dockerfile multi-stage (`uv sync --frozen --no-dev`), `USER app` não-root, `HEALTHCHECK` batendo `/health`, `EXPOSE 8000`; compose com healthcheck por serviço + volume nomeado MySQL.
  - `domain/fastapi-production-patterns` — `workers/settings.py` define `WorkerSettings` (arq) com `redis_settings` lendo de env; sem job de domínio (skeleton).
- **Descrição:** `Dockerfile` multi-stage para a API. `workers/settings.py` define o `WorkerSettings` do arq apontando para Redis (lista de funções vazia/placeholder — sem job de domínio). `infra/docker-compose.yml` (D-05) sobe: `api` (uvicorn `--workers 1` em dev, expõe 8000 direto — D-06), `worker` (arq), `mysql:8.0` (volume nomeado, `--character-set-server=utf8mb4`), `redis`. Healthchecks por serviço; `api`/`worker` com `depends_on: condition: service_healthy`. O `HEALTHCHECK` do Docker bate em `/health` (raiz). `.env.example` consumido. `infra/nginx/jaxego.conf` documenta o reverse proxy de produção (não usado no compose de dev — D-06).
- **Success:** `docker compose -f infra/docker-compose.yml up -d` sobe os 4 serviços saudáveis; `curl -f localhost:8000/health` → exit 0; `docker compose ps` mostra mysql/redis healthy; worker arq conecta ao Redis sem erro.
- **Estimate:** ~2.5h
- **Depends on:** T-02, T-03

### T-05 — Endpoint GET /health com checagem de MySQL e Redis + testes

- **Type:** new_endpoint
- **Files:** `apps/api/app/api/v1/health.py`, `apps/api/tests/conftest.py`, `apps/api/tests/test_health.py`
- **Skills aplicadas:**
  - `domain/fastapi-production-patterns` — router magro; schema Pydantic v2 `HealthRead` com `ConfigDict(from_attributes=True)`; `conftest.py` com fixtures `app`/`client` (httpx ASGITransport).
  - `quality/observability-production` — `/health` é o health endpoint; valida emissão de log estruturado da request com `duration_ms`.
  - `product/api-design-contracts` — contrato de resposta padronizado do health (`{ status, db, redis, version }`); o probe é exposto na **raiz** em `GET /health` (sem prefixo `/v1`), convenção de Docker/Nginx/k8s e caminho exercido pelo HEALTHCHECK e pelo CI (`curl -f localhost:8000/health`).
  - `quality/senior-quality-bar` — sem N+1 (health usa `SELECT 1` + `redis.ping()`); sem PII no payload nem no log.
- **Descrição:** `GET /health` (D-03) é exposto na **raiz**, sem prefixo `/v1` (convenção de health/readiness probe de Docker/Nginx/k8s; é o caminho exercido pelo `HEALTHCHECK` do Docker e pelo CI). Executa `SELECT 1` via engine async e `redis.ping()`; retorna `{ status, db: "ok|down", redis: "ok|down", version }`; 200 quando ambos ok, 503 quando algum down. O handler pode opcionalmente também ser montado em `/v1/health` para consumo versionado, mas o caminho canônico é `/health`. `conftest.py` com fixtures de app e client async. `test_health.py`: (a) 200 em `GET /health` com db/redis ok (usa serviços do compose/CI), (b) payload tem os campos esperados, (c) request emite log com `request_id`.
- **Success:** `uv run pytest tests/test_health.py` passa; `curl -f localhost:8000/health` retorna 200 com `db: ok, redis: ok`.
- **Estimate:** ~1.5h
- **Depends on:** T-02, T-03

### T-06 — Sentry condicional: teste de no-op vs DSN presente

- **Type:** test
- **Files:** `apps/api/tests/test_health.py` (extensão), `apps/api/app/core/observability.py` (ajuste se necessário)
- **Skills aplicadas:**
  - `quality/observability-production` — Sentry init condicional por DSN; no-op em dev sem quebrar; scrubbing default.
  - `owasp-security` (leve) — DSN tratado como segredo (só via env, nunca no repo).
  - `quality/senior-quality-bar` — "segredo no repo" = FAIL-BLOCK: DSN só via env, teste usa DSN fake mockado (nenhuma credencial real no código de teste).
- **Descrição:** Teste que prova: sem `SENTRY_DSN` → `init_sentry()` não inicializa SDK (no-op) e app sobe normal; com DSN fake setado → `init_sentry()` chama `sentry_sdk.init` sem levantar exceção (mock do init para não enviar tráfego real). Garante D-08.
- **Success:** `uv run pytest -k sentry` passa nos dois cenários (com e sem DSN).
- **Estimate:** ~0.75h
- **Depends on:** T-02

### T-07 — Guard de naive datetime em código de domínio (TD-010)

- **Type:** test
- **Files:** `apps/api/tools/check_naive_datetime.py`, `apps/api/tests/test_naive_datetime_guard.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — timestamps UTC; reforça que toda datetime de domínio é timezone-aware (consistente com `DATETIME(6)` UTC).
  - `quality/observability-production` — falha do guard reportada de forma acionável (qual arquivo/linha viola).
- **Descrição:** `tools/check_naive_datetime.py` faz análise AST de `apps/api/app/` procurando padrões proibidos em código de domínio: `datetime.now()` sem `tz`, `datetime.utcnow()`, e `.replace(tzinfo=None)` (o bug exato auditado na v1.0 — `grace_boundary.replace(tzinfo=None)`). Permite `datetime.now(timezone.utc)`/`datetime.now(tz=...)`. `test_naive_datetime_guard.py` roda o guard sobre o código real (deve passar — código nascido limpo) e sobre snippets sintéticos proibidos (deve detectar). Esse guard é o ponto de vigilância que as phases 2/7/9/10/11 herdam (TD-010, D-10).
- **Success:** `uv run pytest tests/test_naive_datetime_guard.py` passa; o guard detecta `.replace(tzinfo=None)` e `datetime.utcnow()` em snippet de teste e aprova o código do projeto.
- **Estimate:** ~1.5h
- **Depends on:** T-01

### T-08 — Pipeline GitHub Actions (lint + typecheck + test)

- **Type:** infra
- **Files:** `.github/workflows/ci.yml`
- **Skills aplicadas:**
  - `domain/github-actions-ci` — pipeline canônico: `astral-sh/setup-uv@v5`, `uv sync --frozen` (lockfile divergente = erro), MySQL 8.0 + Redis como `services`, `alembic upgrade head` no CI, `concurrency` + `cancel-in-progress`; jobs `lint`/`typecheck`/`test`.
  - `meta/orchestration-decision-tree` — domínio "CI/CD" → skill `github-actions-ci` obrigatória (matriz por camada do CLAUDE.md).
- **Descrição:** `ci.yml` em push/PR (D-09). Jobs: `lint` (`uv run ruff check .` + `uv run ruff format --check .`), `typecheck` (`uv run basedpyright`), `test` (services mysql:8.0 + redis; `uv run alembic upgrade head`; `uv run pytest -q` — inclui health + sentry + guard de naive datetime). O smoke do CI bate em `curl -f localhost:8000/health` quando aplicável. `concurrency` com `cancel-in-progress`. Build/deploy por tag fica como esqueleto comentado/documentado (deploy real é Phase 14). `.python-version` 3.13 respeitado pelo setup-uv.
- **Success:** Pipeline verde no commit inicial; os 3 jobs passam; um PR com lockfile divergente ou naive datetime em domínio faz o CI falhar (red comprova o guard).
- **Estimate:** ~1.5h
- **Depends on:** T-05, T-06, T-07

### T-09 — Checkpoint: verificação humana da fundação rodando

- **Type:** checkpoint:human-verify
- **What-built:** Stack completa subindo via Docker Compose, `/health` verde, pipeline CI verde.
- **How-to-verify:**
  1. `docker compose -f infra/docker-compose.yml up -d` — aguardar containers healthy (`docker compose ps`).
  2. `curl -i localhost:8000/health` — esperar HTTP 200 com `db: ok, redis: ok` e header `X-Request-ID`.
  3. `docker compose logs api | tail -5` — confirmar logs JSON com `request_id`, `endpoint`, `duration_ms` e SEM nenhum campo PII.
  4. Conferir o run mais recente do workflow CI no GitHub Actions — os 3 jobs (lint, typecheck, test) verdes.
- **Resume-signal:** Digite "aprovado" ou descreva o que falhou.
- **Depends on:** T-04, T-08

---

## Execution order

Waves (grupos paralelizáveis — `parallelization.plan_level: true`, `task_level: false`, `max_concurrent_agents: 3`):

- **Wave 1:** T-01 (raiz: pyproject/uv/config — bloqueia tudo).
- **Wave 2 (paralelo):** T-02 (app factory + observability), T-03 (DB/Alembic), T-07 (guard naive datetime) — todos dependem só de T-01, sem conflito de arquivos.
- **Wave 3 (paralelo):** T-05 (health + testes, depende de T-02+T-03), T-06 (sentry test, depende de T-02). T-04 (Docker Compose, depende de T-02+T-03) também pode entrar aqui mas toca infra isolada — sem conflito de arquivos com T-05/T-06.
- **Wave 4:** T-08 (CI, depende de T-05+T-06+T-07).
- **Wave 5:** T-09 (checkpoint humano, depende de T-04+T-08).

> **parallel-hint conservador:** Wave 2 e Wave 3 são as únicas com paralelismo real; cada task tem ownership exclusivo de arquivos (T-05 só estende `test_health.py`/`conftest.py`, T-06 estende `test_health.py` — para evitar conflito no mesmo arquivo, T-06 roda **após** T-05 ou edita bloco distinto; preferir sequência T-05 → T-06 se executor único). `task_level: false` na config significa que o paralelismo é entre planos, não entre tasks de um mesmo plano — em dúvida, executar as waves em sequência.

---

## Reconciliation expectations

Ao fim da execução, o `/gsd:reconcile-state 1` verifica:

- Todos os arquivos de `files_modified` existem.
- `create_app()` existe em `main.py` e registra middleware + router `/v1` + handler de erro.
- `GET /health` (raiz, sem prefixo `/v1`) tem handler que toca MySQL (`SELECT 1`) e Redis (`ping`).
- Middleware emite os 6 campos obrigatórios de log; nenhum campo PII presente.
- Migration baseline existe e é vazia (sem tabela de domínio).
- `ci.yml` tem os 3 jobs (lint/typecheck/test) e roda o guard de naive datetime.
- `tools/check_naive_datetime.py` existe e é exercido por teste.
- Nenhum arquivo-fantasma; nenhuma feature de domínio/auth/UI (fora de escopo).

Divergências entram em `RECONCILIATION.md` antes de fechar a fase.

---

## Rollback plan

Greenfield — rollback é trivial:
- Revert dos commits `feat(phase-1/...)` da fundação.
- `docker compose -f infra/docker-compose.yml down -v` (remove volume MySQL nomeado).
- Sem migrations de domínio a reverter (baseline vazia); `alembic downgrade base` se necessário.
- Sem ações de ops em produção (deploy é Phase 14).

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | ausente | incompleto}
- Performance budget: {presente | N/A | incompleto}
- Observability checklist: {presente | N/A | incompleto}
- Integration contracts: {presente | N/A | incompleto}
- Revision iteration: {1 | 2 | 3 | final}
