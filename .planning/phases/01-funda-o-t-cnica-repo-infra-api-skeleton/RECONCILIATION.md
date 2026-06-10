# RECONCILIATION — Phase 1: Fundação técnica

**Data:** 2026-06-10
**Método:** comparação PLAN.md (prometido) × código real + verificação ao vivo (docker compose up + smoke)

---

## Prometido vs. Entregue

| Item do PLAN | Prometido | Real (código) | Status |
|---|---|---|---|
| T-01 Monorepo + uv | `apps/api/`, pyproject, `.python-version` 3.13, ruff/pyright/pytest config | `apps/api/` com pyproject, uv.lock, `.python-version`, `.gitattributes` | ✅ |
| T-02 App factory + obs | `create_app()`, middleware request_id+duração, logs JSON 6 campos, Sentry condicional | `app/main.py`, middleware, logging estruturado, Sentry no-op sem DSN | ✅ |
| T-03 DB + Alembic | SQLAlchemy 2 async, Base/metadata c/ naming convention, Alembic baseline vazia, utf8mb4/UTC | `app/db/`, `alembic/`, migration `0001` baseline, naming convention | ✅ |
| T-05 `/health` | endpoint na raiz, checa MySQL (`SELECT 1`) + Redis ping, `{status,db,redis,version}` | `app/api/v1/health.py` montado na raiz `/health` | ✅ (verificado: 200 ao vivo) |
| T-06 Sentry | no-op sem DSN, init com DSN | testado (no-op vs DSN) | ✅ |
| T-04 Worker + Compose | arq worker, compose api/worker/mysql8/redis com healthchecks, Nginx doc | `infra/docker-compose.yml`, `infra/nginx/`, worker arq | ✅ (verificado: stack healthy ao vivo) |
| T-07 Guard naive datetime (TD-010) | check AST + teste pegando `.replace(tzinfo=None)` | `apps/api/tools/check_naive_datetime.py` + testes | ✅ |
| T-08 CI | GitHub Actions lint+typecheck+test | `.github/workflows/ci.yml` | ⏳ (não verificado em execução remota — sem GitHub remote ainda) |
| T-09 Checkpoint humano | docker up + curl /health 200 + worker up | **verificado ao vivo por Claude (autorizado pelo dono)** | ✅ |

---

## Desvios detectados e resolução

1. **Bug runtime DB (pego no smoke ao vivo):** MySQL 8 usa `caching_sha2_password`; faltava o pacote `cryptography`. `/health` retornava 503 `db:down`. → **Corrigido** (`2e5f9b6`): `cryptography>=43,<46` adicionado, lockfile atualizado. Re-smoke: `db:ok`.
2. **Bug runtime worker (pego no smoke ao vivo):** `WorkerSettings.functions=[]` → arq recusa boot. → **Corrigido** (`34682b3`): task `healthcheck` registrada + teste de regressão. Re-smoke: worker Up.
3. **Reconciliação health endpoint:** plano inicial usava `/v1/health`; reconciliado para `/health` na raiz (convenção infra, bate com verificação do ROADMAP). Aplicado antes da execução.
4. **Estrutura:** README do projeto em `apps/api/README.md` (raiz é README do framework — não sobrescrever). `.gitattributes` adicionado (normalização LF/CRLF p/ CI no Windows).

**Lição (vale registrar):** testes unitários com DB/Redis mockados deram 17/20 verdes mas NÃO pegaram os 2 bugs de integração runtime. O smoke ao vivo (docker compose) foi o que validou de verdade — reforça o valor do checkpoint T-09 e do `integration_check` nas phases seguintes.

---

## Gates

| Gate | Status |
|---|---|
| Gate 7 (tests + lint) | ✅ ruff/pyright limpos, pytest 20 passed |
| Gate 6 (reconciliation) | ✅ este documento, sem gaps abertos |
| Smoke ao vivo (T-09) | ✅ /health 200, db:ok, redis:ok, worker Up |

**Pendência não-bloqueante:** CI verde em execução remota (T-08) só será confirmável quando houver GitHub remote + push (não há remote configurado). Registrado abaixo.

## Atualizações de estado
- TD a registrar: nenhuma nova dívida de código. Pendência operacional: configurar GitHub remote para validar o pipeline CI ao vivo (rastreado como item de release/Phase 14, não bloqueia MS-01).
