# RECONCILIATION — Phase 2: Núcleo multi-área + autenticação + RBAC

**Data:** 2026-06-10
**Método:** PLAN.md (prometido) × código real + verificação ao vivo contra MySQL 8

---

## Prometido vs. Entregue

| Área | Prometido (PLAN) | Real (código) | Status |
|---|---|---|---|
| Schema multi-área | areas, users(global), area_admins, audit_log, refresh_tokens + utf8mb4 + naming convention | migration `0002_core_auth_multiarea` (5 tabelas) | ✅ |
| Append-only (RN-012) | trigger MySQL nega UPDATE/DELETE em audit_log (SIGNAL 45000) | `trg_audit_log_no_update`, `trg_audit_log_no_delete` | ✅ **verificado ao vivo: UPDATE/DELETE → errno 1644** |
| argon2id (D-02) | params explícitos pinados (não "custo 12" bcrypt) | `core/security.py` time_cost=2/memory=19456/parallelism=1 + benchmark | ✅ (LOW-1 resolvido) |
| JWT (D-01) | HS256, alg pinado no decode, claims obrigatórias, refresh opaco rotacionável + reuse detection | PyJWT, `algorithms=["HS256"]`, refresh sha256 em DB, revoga família no reuso | ✅ (LOW-2 resolvido) |
| TOTP (D-03) | pyotp, obrigatório admin plataforma, anti-replay | enroll/verify, valid_window | ✅ |
| Lockout (D-04) | 5/15min → 423/429, anti-enumeração, aware UTC | service de login + lockout | ✅ (teste HTTP verde) |
| Isolamento multi-área (D-05/06) | area_id em domínio, escopo no token, cross-área → 403, bypass admin auditado | AreaScoped mixin + dependency area_scope + repository WHERE area_id; bypass → audit_log | ✅ (teste isolamento verde) |
| RBAC (D-08/09) | 6 papéis via dependencies, resolve por contexto de área | require_role / require_platform_admin | ✅ |
| LGPD (D-12) | PII marcada, CPF mascarado, anonimização como schema/flags | modelos + flags | ✅ (jobs efetivos → Phase 14) |
| Endpoints | /v1/auth/login|refresh|logout, /v1/auth/totp/*, /v1/areas | routers registrados | ✅ |

---

## Critérios de aceite do ROADMAP

| Critério | Resultado |
|---|---|
| Isolamento: seed 2 áreas, cross-área → 403 | ✅ teste HTTP verde |
| Trigger: UPDATE em audit_log → erro MySQL | ✅ **ao vivo: errno 1644 SIGNAL 45000** (UPDATE e DELETE) |
| Lockout: 6ª tentativa/15min → 423/429 | ✅ teste verde |

---

## Desvios e bugs corrigidos

1. **Bug de deploy (pego no live MySQL):** trigger não nascia — MySQL 8 com binlog exige `log_bin_trust_function_creators=1` (ou SUPER) para usuário de app criar trigger (errno 1419). → **Corrigido** (`c8dafe2`): flag adicionada ao serviço mysql do compose + nota para o VPS de produção. Re-verificado: triggers criados e enforçando.
2. **Flaky de teste (Windows):** `pytest -m mysql` falhava por `Event loop is closed` no teardown de `aiomysql.Connection.__del__`. → **Corrigido** (`b0ce439`): fixture `mysql_engine` dedicada com `NullPool` + `await engine.dispose()` no mesmo loop. 3/3 mysql verdes.
3. **Rule 2:** senha mínima de 10 chars (política do threat model, NIST 800-63B) — `af40e5b`.
4. **Rule 3:** `email-validator` (EmailStr), `aiosqlite` (testes), variant BIG_ID p/ SQLite.
5. **Rule 1 (TD-010):** `ensure_aware_utc()` no boundary de leitura do DB; commit no service para persistir estado de segurança (lockout/revogação) mesmo no caminho de exceção.

---

## Gates

| Gate | Status |
|---|---|
| Gate 3 (Skills) | ✅ PASS (8/8 skills, 1ª iteração) |
| Gate 4 (Security Baseline) | ✅ 10 ameaças mapeadas no RESEARCH → threat model do PLAN |
| Gate 7 (tests+lint) | ✅ 66 not-mysql + 3 mysql passed; ruff/pyright limpos |
| Gate 6 (reconciliation) | ✅ este documento, sem gaps |
| Gate 8 (senior-quality-bar) | ✅ sem FAIL-BLOCK: JWT_SECRET só env, toda rota com dependency de auth, PII fora de log, SQL parametrizado |

---

## Pendências / follow-up (não-bloqueantes)
- **Smoke de auth-flow ao vivo contra MySQL** (login→token→refresh→cross-área 403 com dados reais) ainda não rodado end-to-end porque não há admin de plataforma semeado. Cobertura atual: 66 testes HTTP (SQLite) + conectividade MySQL + trigger ao vivo. → Validar quando houver seed de admin (necessário na Phase 4, onboarding). Rastreado aqui; baixo risco (auth é Python puro + datetime aware tratado).
- CI verde em execução remota (jobs lint/typecheck/test) ainda depende de configurar GitHub remote (item de release/Phase 14). O job de teste do CI precisa subir MySQL 8 service container para os testes `@mysql` (LOW-3) — o workflow já referencia isso; confirmar quando houver remote.
