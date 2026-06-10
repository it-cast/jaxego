# Phase 1: Fundação técnica (repo, infra, API skeleton) - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega a fundação técnica do monorepo: estrutura de pastas, backend FastAPI mínimo rodando com `/health`, Docker Compose (api, worker, mysql, redis), Alembic configurado, observabilidade base (logs estruturados + request_id + Sentry wired) e pipeline GitHub Actions verde (lint + typecheck + test). **Não** entrega nenhuma regra de negócio, entidade de domínio, autenticação ou UI — isso são as phases 2+.
</domain>

<decisions>
## Implementation Decisions

### Estrutura do repositório
- **D-01:** Monorepo único. Backend em `apps/api/` (FastAPI), frontend virá em `apps/web/` na Phase 3. Pasta `infra/` para Docker Compose e Nginx; `.github/workflows/` para CI. [auto] recomendado — coerente com "1 código, 3 superfícies" (`stack.md:27`) e shared-DB ADR-001.
- **D-02:** Gerenciamento de pacotes Python com `uv`; Python pinado em **3.13** via `.python-version` (sistema tem 3.12 — `uv` instala/usa 3.13). Lockfile `uv.lock` versionado. [auto] recomendado (ADR-002, `stack.md:9,16`).

### Backend skeleton
- **D-03:** FastAPI 0.115 com app factory (`create_app()`), router `/v1` versionado por prefixo (DRV-003), e endpoint `GET /health` retornando status + checagem de MySQL e Redis. [auto] recomendado.
- **D-04:** SQLAlchemy 2.x + Alembic configurados desde já (engine async), `utf8mb4`, timestamps UTC; convenção de naming de constraints definida no metadata. Nenhuma tabela de domínio nesta phase — apenas a infraestrutura de migrations e uma migration inicial vazia/baseline. [auto] recomendado (DRV-002, `stack.md:11-13`).

### Infraestrutura local (Docker Compose)
- **D-05:** Um `docker-compose.yml` sobe: `api` (FastAPI/uvicorn), `worker` (arq), `mysql:8.0`, `redis`. Healthchecks por serviço; volumes nomeados para MySQL. `.env.example` versionado, `.env` ignorado. [auto] recomendado (`stack.md:31-34`).
- **D-06:** Nginx fica documentado/configurado como reverse proxy para produção, mas o compose de dev expõe a API direto. [auto] recomendado (escopo mínimo do M1).

### Observabilidade base
- **D-07:** Logs estruturados JSON em stdout com os campos obrigatórios de `config.json > observability.required_log_fields` (request_id, user_id, endpoint, method, status_code, duration_ms). Middleware de request_id + duração. PII proibida em log (lista de `pii_fields_forbidden_in_logs`). [auto] recomendado (REQ-050, `quality/observability-production`).
- **D-08:** Sentry SDK instalado e inicializado condicionalmente por `SENTRY_DSN` (sem DSN → no-op, não quebra dev). [auto] recomendado.

### CI/CD
- **D-09:** GitHub Actions com jobs: `lint` (ruff check + format check), `typecheck` (basedpyright), `test` (pytest). Trigger em push/PR. Build/deploy por tag fica como esqueleto documentado (deploy real é Phase 14). [auto] recomendado (REQ-052, `domain/github-actions-ci`).

### Guard de qualidade desde o commit 1
- **D-10:** Lint custom/teste proibindo naive datetime em código de domínio já previsto como hook/teste a partir desta fundação (TD-010 — lição auditada da v1.0). [auto] recomendado.

### Claude's Discretion
- Layout exato de submódulos dentro de `apps/api/` (ex.: `core/`, `db/`, `api/v1/`).
- Escolha entre `structlog` e logging stdlib + formatter JSON (ambos atendem D-07).
- Nome e conteúdo exato da migration baseline.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stack e infra
- `projeto/stacks/stack.md` §Backend, §Infra — versões travadas, serviços, orçamentos
- `.planning/DECISIONS.md` — ADR-002 (backend), DRV-002 (convenções de banco), DRV-003 (convenções de API)

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-052 (infra Docker+CI), REQ-050 (observabilidade), REQ-022 (migrations/convenções)

### Regras transversais
- `projeto/regras-negocio/regras.md` §Convenções transversais (`:40-42`) — API, banco, frontend
- `.planning/TECH-DEBT.md` — TD-010 (naive datetime, pre_launch_high, vigilância desde a fundação)

### Config operacional
- `.planning/config.json` — `observability` (campos de log, PII proibida), `performance_budget`, `ci_gates`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Nenhum código de aplicação ainda (greenfield). `apps/` ainda não existe.

### Established Patterns
- Convenções já fixadas em docs: `/v1/` prefix, RFC 7807 errors, cursor pagination, idempotência por header (DRV-003); soft delete + FK RESTRICT + utf8mb4 + UTC (DRV-002).

### Integration Points
- Esta phase cria os pontos de integração que todas as outras consomem: app factory, sessão de DB, conexão Redis, config por env, pipeline CI.
</code_context>

<specifics>
## Specific Ideas

- Atenção explícita a naive datetime desde o início (`grace_boundary.replace(tzinfo=None)` foi bug auditado na v1.0 do grupo — `stack.md:58`, `regras.md:41`). Timestamps UTC no banco, conversão só na borda.
- p95 < 200ms em endpoints quentes e LCP < 2,5s são orçamentos do projeto — a fundação não pode introduzir overhead estrutural.
</specifics>

<deferred>
## Deferred Ideas

- Deploy real (VPS, tags, Nginx em produção) — Phase 14 (release).
- Infra de LLM (router + ai_usage_log) — Phase 14 (REQ-053).
- Qualquer entidade de domínio, auth, RBAC — Phase 2.
</deferred>

---

*Phase: 01-funda-o-t-cnica-repo-infra-api-skeleton*
*Context gathered: 2026-06-10*
