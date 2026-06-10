# EXECUTION-LOG — Phase 1 Plan 01-01: Fundação técnica

> Executor: gsd-executor (Claude Opus 4.8)
> Início: 2026-06-10T12:48Z · Fim (T-08): 2026-06-10T12:59Z
> Branch: master · Plano: `.planning/phases/01-funda-o-t-cnica-repo-infra-api-skeleton/PLAN.md`
> Escopo executado: **T-01 → T-08**. **T-09 NÃO executado** (checkpoint humano, `autonomous: false`).

---

## Tasks concluídas

| Task | Tipo | Wave | Commit | Resumo |
|------|------|------|--------|--------|
| T-01 | infra | W1 | `e3648dd` | Monorepo `apps/api/`, uv + pyproject (deps travadas), `.python-version` 3.13, `uv.lock`, `core/config.py`, `.env.example`, `.gitattributes` |
| T-02 | endpoint skeleton | W2 | `e3fd29a` | `create_app()`, `RequestContextMiddleware` (request_id + duration + 6 campos), structlog JSON, Sentry condicional, `AppError` + handler RFC-7807-like, router `/v1` |
| T-03 | migration | W2 | `4491b5c` | `Base`/metadata (naming convention, utf8mb4), engine async (aiomysql) + sessionmaker, Alembic async, baseline `0001` vazia |
| T-07 | test | W2 | `95923ab` | Guard AST de naive datetime (TD-010) + 9 testes |
| T-05 | endpoint | W3 | `90b25da` | `GET /health` (raiz) SELECT 1 + redis.ping, contrato `{status,db,redis,version}`, conftest + 5 testes |
| T-06 | test | W3 | `eb2bf00` | Sentry no-op vs DSN fake (3 testes) |
| T-04 | infra | W3 | `051ea62` | Worker arq, Dockerfile multi-stage não-root + HEALTHCHECK, `docker-compose.yml` (api/worker/mysql:8.0/redis), `nginx/jaxego.conf` |
| T-08 | infra | W4 | `8ec94e6` | CI GitHub Actions: jobs lint / typecheck / test (services mysql+redis, alembic upgrade head, guard) |

## T-09 — checkpoint humano (PENDENTE)

`type: checkpoint:human-verify`, `autonomous: false`. Não executado pelo agente.
Requer subir a stack e validar no GitHub Actions (ver seção "Validação humana").

---

## Resultado da verificação local (gate 7)

Rodado a partir de `apps/api/`:

- `uv sync --frozen` → 45 pacotes, sem divergência de lockfile. **Sem conflito arq+redis** (arq resolveu redis 5.3.1).
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **26 files already formatted**
- `uv run basedpyright` → **0 errors, 0 warnings, 0 notes**
- `uv run pytest` → **17 passed** (5 health + 3 sentry + 9 guard)
- `uv run python tools/check_naive_datetime.py` → **OK: no naive datetime in domain code**
- `uv run alembic upgrade head --sql` (offline) → cadeia de migration válida (baseline aplica/reverte)
- `docker compose -f infra/docker-compose.yml config` → **válido (exit 0)**

> Não rodado localmente (escopo do checkpoint T-09): `docker compose up` real e o run remoto do CI.

---

## Desvios do plano

1. **`README.md` do projeto criado em `apps/api/README.md`** (não na raiz). Motivo: o `README.md` da raiz é a documentação do gsd-framework; sobrescrevê-lo violaria o contrato (CLAUDE.md). O pyproject referencia o README do pacote. Rule 3 (resolver bloqueio sem destruir artefato existente).
2. **Teste do Sentry em `tests/test_sentry.py`** (não como extensão de `test_health.py`). Motivo: o próprio PLAN (nota de parallel-hint) permite "editar bloco distinto" para evitar conflito no mesmo arquivo; arquivo separado é mais limpo e isola ownership. Sem impacto funcional.
3. **`.gitattributes` adicionado** (não listado em `files_modified`). Motivo: Windows converte LF→CRLF; sem normalização, `ruff format --check` falharia no CI. Rule 2 (funcionalidade crítica para o gate de lint passar cross-platform).
4. **`uvicorn[standard]` e `pymysql` adicionados às deps.** Motivo: uvicorn é necessário para o `CMD` do Dockerfile e o comando de dev (`uv run uvicorn`); pymysql veio transitivo via aiomysql/alembic sync. Rule 3 (dependência necessária para rodar a app).
5. **Tudo de `apps/api/` (pyproject, uv.lock, .env.example a nível raiz).** `.env.example` ficou na raiz (D-05 pede `.env.example` versionado na raiz, consumido pelo compose); demais artefatos Python sob `apps/api/` conforme D-01.

Nenhum desvio arquitetural (Rule 4). Nenhuma tabela de domínio/auth/UI criada (fora de escopo respeitado).

---

## Stubs conhecidos (intencionais, fundação)

- `app/api/v1/router.py` — `api_router` sem sub-rotas (domínio entra na Phase 2).
- `app/workers/settings.py` — registra apenas `healthcheck` (heartbeat mínimo); jobs de domínio entram na Phase 2. ~~`functions: []`~~ corrigido no smoke (ver abaixo): lista vazia fazia o arq crashar no boot.
- `alembic/versions/0001_baseline.py` — `upgrade`/`downgrade` vazios (REQ-022: sem schema de domínio).

Todos previstos pelo PLAN/CONTEXT como skeleton da fundação.

---

## Fixes pós-smoke (T-09, docker compose up real)

> Data: 2026-06-10 · Executor: gsd-executor (Claude Opus 4.8)
> O smoke ao vivo (docker compose up real) revelou 2 bugs de runtime que o pytest com mocks não pegou.

| Bug | Commit | Resumo |
|-----|--------|--------|
| BUG 1 — `/health` → 503 (db:down) | `2e5f9b6` | `RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods`. MySQL 8.0 usa `caching_sha2_password` por padrão e aiomysql/pymysql precisam de `cryptography` para o handshake. Fix: `cryptography>=43,<46` adicionado às deps de `apps/api`; `uv.lock` atualizado (resolveu `cryptography==45.0.7`, `cffi`, `pycparser`). **Auth plugin do MySQL 8 mantido no default seguro** — sem downgrade para `mysql_native_password`. |
| BUG 2 — worker arq em crash loop (Restarting 1) | `34682b3` | `RuntimeError: at least one function or cron_job must be registered` em `WorkerSettings` com `functions=[]`. Fix: criada task mínima `async def healthcheck(ctx) -> str` em `app/workers/tasks.py` e registrada em `WorkerSettings.functions`. Novo teste `tests/test_worker_settings.py` (3 testes) garante ≥1 função registrada — gate 7 protege contra regressão. |

### Verificação local pós-fix (gate 7)

Rodado a partir de `apps/api/`:

- `uv lock` + `uv sync` → consistentes; `cryptography==45.0.7` no `uv.lock` (versionado).
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **28 files already formatted**
- `uv run basedpyright` → **0 errors, 0 warnings, 0 notes**
- `uv run pytest` → **20 passed** (17 anteriores + 3 do worker)

> `docker compose up` real e re-teste do smoke ficam a cargo do humano (não rodado pelo agente, conforme escopo do checkpoint T-09).
