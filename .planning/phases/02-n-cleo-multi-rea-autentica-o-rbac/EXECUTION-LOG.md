# EXECUTION-LOG — Phase 2: Núcleo multi-área + autenticação + RBAC

**Executed:** 2026-06-10
**Plan:** `.planning/phases/02-n-cleo-multi-rea-autentica-o-rbac/PLAN.md`
**Platform:** Windows, uv 0.11.6, Python 3.13 (uv), reusando infra da Phase 1.
**Result:** 16/16 tasks concluídas. Gates locais (ruff/format/pyright/pytest) verdes.

---

## Tasks concluídas (T-01..T-16) e commits

| Task | Descrição | Commit |
|------|-----------|--------|
| T-01 | AreaScoped mixin + scoped base repository + skeletons (auth/areas/audit) | `f298a56` |
| T-02 | Core security argon2id (params explícitos OWASP, LOW-1) + TOTP + JWT_SECRET config | `e707203` |
| T-03 | JWT HS256 (alg pinado + claims obrigatórias, anti alg:none) + refresh opaco (LOW-2) | `d5d9be9` |
| T-04 | Models User/RefreshToken/Area/AreaAdmin/AuditLog + write_audit | `b710a5d` |
| T-05 | Auth service login + lockout (aware UTC) + anti-enumeração + TOTP | `6dd2129` |
| T-05b | Fix: LoginBody senha mín. 10 chars (NIST/A07) [Rule 2] | `af40e5b` |
| T-06 | Areas service (CRUD + soft-archive) + RBAC resolve_role | `bf965e1` |
| T-11+T-12 | Migration 0002 schema (5 tabelas) + triggers append-only (op.execute, dialect guard, LOW-3) | `fca2319` |
| T-07 | Refresh rotação + detecção de reuso (revoga família) + logout | `58e751e` |
| T-08 | Auth router /v1/auth/login\|refresh\|logout + registro em /v1 | `ef350a9` |
| T-09 | Auth dependencies (get_current_user/area_scope/require_role/require_platform_admin) + TOTP enroll/verify | `274e37c` |
| T-10 | Areas router /v1/areas CRUD (platform-admin only) + bypass auditado | `aa6b3c7` |
| T-13..T-16 | Testes de aceite + fixtures + marker mysql + fixes de datetime/persistência | `1b936f2` |

> T-11 e T-12 compartilham um único arquivo de migration (`0002_core_auth_multiarea.py`), logo foram commitados juntos. Os triggers append-only (T-12) estão no `upgrade()` com guarda de dialeto MySQL e o `downgrade()` dropa os triggers antes das tabelas.

---

## Verificação local (Gate 7)

- `uv sync` — consistente (54 pacotes).
- `uv run ruff check .` — **All checks passed**.
- `uv run ruff format --check .` — **55 files already formatted**.
- `uv run basedpyright` — **0 errors, 0 warnings, 0 notes**.
- `uv run pytest -m "not mysql"` — **66 passed, 3 deselected** (os 3 são `@pytest.mark.mysql`).
- `uv run alembic upgrade head` / `downgrade base` — limpos em SQLite (triggers MySQL-gated).

### Libs adicionadas (pyproject + uv.lock)
- `argon2-cffi>=25,<26` (25.1.0)
- `pyjwt>=2.10,<3` (2.13.0)
- `pyotp>=2.9,<3` (2.9.0)
- `email-validator>=2,<3` (2.3.0) — exigido por Pydantic `EmailStr` [Rule 3]
- `aiosqlite>=0.20,<1` (dev) — testes rodam contra SQLite in-memory sem MySQL [Rule 3]

---

## Testes que EXIGEM MySQL 8 real (rodar ao vivo para fechar verificação)

Marcados `@pytest.mark.mysql` em `tests/test_audit_append_only.py` (REQ-004 / RN-012 / TH-10).
Pré-requisito: migration 0002 aplicada contra MySQL 8 (`uv run alembic upgrade head` com `DATABASE_URL` apontando para o MySQL real), o que cria os triggers `trg_audit_log_no_update` / `trg_audit_log_no_delete`.

```bash
cd apps/api
# (garantir DATABASE_URL -> MySQL 8 real e migration aplicada)
uv run alembic upgrade head
uv run pytest -m mysql tests/test_audit_append_only.py -x
```

Asserções:
- INSERT em `audit_log` → OK
- UPDATE em `audit_log` → erro MySQL `SIGNAL SQLSTATE '45000'` (errno 1644)
- DELETE em `audit_log` → erro MySQL `SIGNAL SQLSTATE '45000'`

> Os critérios de aceite do ROADMAP **isolamento (403)** e **lockout (423)** JÁ rodam verdes contra SQLite/HTTP na suíte local (`tests/test_area_isolation.py`, `tests/test_auth_lockout.py`). Apenas o **trigger append-only** depende de MySQL real (sintaxe MySQL-específica) e fica pendente de execução ao vivo do orquestrador.

LOW-3: como o trigger só roda contra MySQL, se a verificação ao vivo não for executada no fechamento da phase, registrar TD `pre_launch_high` em `TECH-DEBT.md` (o critério de aceite do ROADMAP depende disso).

---

## Desvios do plano (deviation rules)

| # | Tipo | Descrição | Tasks/Commit |
|---|------|-----------|--------------|
| 1 | Rule 2 (critical) | `LoginBody` passou a exigir senha mín. 10 chars (política NIST/A07 do threat model) | `af40e5b` |
| 2 | Rule 3 (blocking) | Adicionado `email-validator` (Pydantic `EmailStr` não funciona sem) | T-05 |
| 3 | Rule 3 (blocking) | Adicionado `aiosqlite` (dev) para a suíte rodar sem MySQL real | T-13 |
| 4 | Rule 1 (bug) | `ensure_aware_utc()` no boundary de leitura do DB — SQLite/MySQL retornam naive em `DateTime(timezone=True)`, causando `TypeError` naive/aware no lockout/refresh (TD-010) | `1b936f2` |
| 5 | Rule 1 (bug) | `commit()` (não `flush()`) no service para failed-attempt/lockout e revogação de família por reuso — o router não faz commit no caminho de exceção, então o estado de segurança precisa persistir mesmo ao levantar erro | `1b936f2` |
| 6 | Rule 3 (blocking) | `BIG_ID` variant (BIGINT MySQL / INTEGER SQLite) — SQLite só auto-incrementa `INTEGER PRIMARY KEY` | `1b936f2` |
| 7 | Rule 1 (bug, qualidade de teste) | Testes `@mysql` reportavam FAILED por ruído de teardown asyncio no Windows (`RuntimeError: Event loop is closed` em `aiomysql.Connection.__del__`, escalado por `unraisableexception`). Causa raiz: usavam o `engine` process-wide de `app.db.session` (criado em import-time, fora do loop do teste; conexões pooled finalizadas num loop já fechado). Fix: fixture `mysql_engine` dedicada com `NullPool` + `await engine.dispose()` no teardown, dentro do mesmo loop. Sem `filterwarnings ignore` — ciclo de vida corrigido. | `test(02)` |

Todos os fixes têm cobertura de teste. Nenhuma mudança arquitetural (Rule 4) foi necessária.

**Verificação ao vivo do trigger append-only (LOW-3 resolvido):** rodado contra MySQL 8 real
(`DATABASE_URL=mysql+aiomysql://jaxego:jaxego@127.0.0.1:3307/jaxego`): INSERT OK, UPDATE/DELETE
→ errno 1644 / SQLSTATE 45000 (`audit_log is append-only (RN-012)`). `uv run pytest -m mysql -v`
→ **3 passed**. Critério de aceite append-only do ROADMAP confirmado.

---

## Endpoints entregues (sob /v1)

- `POST /v1/auth/login` — TokenPair (access no body + refresh httpOnly+Secure cookie + body)
- `POST /v1/auth/refresh` — rotação (cookie ou body)
- `POST /v1/auth/logout` — revoga + limpa cookie (204)
- `POST /v1/auth/totp/enroll` — secret + provisioning URI (uma vez)
- `POST /v1/auth/totp/verify` — confirma enrolment (204)
- `POST/GET/GET{id}/PATCH/POST{id}/archive /v1/areas` — CRUD restrito a `require_platform_admin`, cross-área auditado

Todas as rotas de domínio passam por dependency de autorização explícita (Gate 8: zero rota órfã).
