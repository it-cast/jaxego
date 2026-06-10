---
phase: 02-n-cleo-multi-rea-autentica-o-rbac
phase_number: 2
plan: PLAN
type: execute
milestone: MS-01
has_ui: false
has_api: true
has_pii: true
integration_check: false
autonomous: true
security_enforcement: true
requirements: [REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-007]
files_modified:
  - apps/api/pyproject.toml
  - apps/api/app/core/config.py
  - apps/api/app/core/security.py
  - apps/api/app/db/mixins.py
  - apps/api/app/db/repository.py
  - apps/api/app/auth/models.py
  - apps/api/app/auth/schemas.py
  - apps/api/app/auth/service.py
  - apps/api/app/auth/dependencies.py
  - apps/api/app/auth/router.py
  - apps/api/app/areas/models.py
  - apps/api/app/areas/schemas.py
  - apps/api/app/areas/service.py
  - apps/api/app/areas/router.py
  - apps/api/app/audit/models.py
  - apps/api/app/audit/service.py
  - apps/api/app/api/v1/router.py
  - apps/api/alembic/versions/0002_core_auth_multiarea.py
  - apps/api/tests/conftest.py
  - apps/api/tests/test_security_argon2.py
  - apps/api/tests/test_jwt.py
  - apps/api/tests/test_auth_flow.py
  - apps/api/tests/test_auth_lockout.py
  - apps/api/tests/test_totp.py
  - apps/api/tests/test_anti_enumeration.py
  - apps/api/tests/test_area_isolation.py
  - apps/api/tests/test_audit_append_only.py
  - apps/api/tests/test_rbac_matrix.py
---

# PLAN — Phase 2 Plan PLAN: Núcleo multi-área + autenticação + RBAC

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Construir a fundação de identidade e isolamento da plataforma sobre o skeleton da Phase 1: tabelas `areas`, `users` (global), `area_admins` e `audit_log` (global, append-only via trigger); autenticação completa (JWT HS256 access 15min + refresh opaco DB rotacionável + argon2id + TOTP + lockout 5/15min); middleware/dependencies de escopo de área e RBAC dos 6 papéis. **SEM UI, SEM cadastro de loja/entregador, SEM entidades de entrega.**

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] **Teste de isolamento (ROADMAP):** seed de 2 áreas, admin da área A consulta recurso da área B → **403**; listagem scoped à área A nunca retorna linha da área B (`uv run pytest tests/test_area_isolation.py -x` exit 0).
- [ ] **Bypass auditado (ROADMAP/RN-001):** admin de plataforma acessa cross-área → 200 **e** uma linha em `audit_log` com `cross_area_bypass=True` (`tests/test_area_isolation.py::test_platform_bypass_audited`).
- [ ] **Teste de trigger (ROADMAP):** `UPDATE` em `audit_log` → erro MySQL `SIGNAL SQLSTATE '45000'`; `DELETE` idem; rodando **contra MySQL 8 real no CI** (`uv run pytest tests/test_audit_append_only.py -x`).
- [ ] **Teste de lockout (ROADMAP):** 6ª tentativa de login em 15 min → **423/429** com datetimes aware UTC (`tests/test_auth_lockout.py`).
- [ ] Login feliz → access JWT(15min) + refresh opaco; refresh rotaciona a cada uso; reuso de refresh já rotacionado revoga a família (`tests/test_auth_flow.py`).
- [ ] Admin plataforma sem TOTP configurado → forçado a configurar no primeiro login (`tests/test_totp.py`).
- [ ] Anti-enumeração: e-mail inexistente e senha errada produzem mesma mensagem genérica e custo de tempo equivalente; colisão de cadastro não revela QUAL dado colide (`tests/test_anti_enumeration.py`).
- [ ] Matriz RBAC: papel sem permissão → 403; `require_platform_admin` como dependency separada (`tests/test_rbac_matrix.py`).
- [ ] Parâmetros argon2id explícitos e pinados no código (não defaults implícitos); benchmark de verify em ~100ms registrado (LOW-1 resolvida).
- [ ] PyJWT fixada; algoritmo `["HS256"]` pinado no decode (anti `alg:none`); nota de RS256-como-ADR-futura registrada (LOW-2 resolvida).
- [ ] Migration Alembic única `0002_core_auth_multiarea` cria `areas`, `users`, `area_admins`, `refresh_tokens`, `audit_log` + triggers, com `utf8mb4`/naming convention herdada; `upgrade`/`downgrade` limpos (downgrade dropa triggers antes das tabelas).
- [ ] `JWT_SECRET` adicionado a `core/config.py` e `.env.example` (placeholder); nunca commitado valor real.
- [ ] Todos os testes relacionados passam (`cd apps/api && uv run pytest`).
- [ ] Lint limpo (`cd apps/api && uv run ruff check .`).
- [ ] Commit atômico por wave com mensagem padronizada.

## REQs referenciados

- REQ-001 — Multi-área shared-DB com `area_id` em tudo; middleware injeta escopo; cross-área → 403; bypass admin auditado.
- REQ-002 — Entidade Área com regras locais configuráveis; CRUD restrito ao admin plataforma; soft-archive (não deletável com entregas).
- REQ-004 — Audit log append-only (trigger nega UPDATE/DELETE; before/after; ator/ts/IP).
- REQ-005 — JWT HS256 15min + refresh opaco DB + argon2id + TOTP + lockout 5/15min.
- REQ-006 — Anti-duplicidade (índices únicos por tipo); mensagem que não revela QUAL dado colide; CPF por área.
- REQ-007 — 6 papéis; matriz de permissões por endpoint; admin de área não vê outras áreas (403).

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a uma ou mais tasks deste plano.

- `meta/orchestration-decision-tree` — **T-00**: decisão de decomposição em waves por dependência (migrations/models → security core → auth service → endpoints → middleware/RBAC → testes de aceite) seguindo a árvore "vertical slice quando há acoplamento estrutural; sequencial quando há dependência de artefato"; `parallel-hint` conservador porque a maioria das tasks toca módulos com contratos compartilhados (`core/security.py`, `db/repository.py`).
- `quality/observability-production` — **T-08, T-09**: todo endpoint `/v1/auth/*` e `/v1/areas/*` loga os 6 campos obrigatórios (`request_id`, `user_id`, `endpoint`, `method`, `status_code`, `duration_ms`); `user_id` preenchido após autenticação (campo já reservado na Phase 1); eventos de auth `login_ok`/`login_fail`/`lockout` emitidos como log estruturado **sem PII** (nada de senha/token/email/cpf — denylist do filtro central); 4xx → WARNING, 5xx → ERROR; query > 100ms (slow_query_threshold) logada WARNING.
- `owasp-security` (auth-and-session, api-input-validation) — **T-02, T-03, T-05, T-07, T-08, T-10**: argon2id (A02); JWT com `algorithms=["HS256"]` pinado + claims obrigatórias no decode (A02, anti `alg:none`); refresh opaco hasheado SHA-256 + rotação + detecção de reuso (A02); `secrets.compare_digest` em comparações de segredo (A02/A08); `WHERE area_id` na query (A01), 404 para recurso de outra área, 403 para admin de área cross-área, `require_platform_admin` como dependency separada (A01); lockout derivado 5/15min (A04/A07); mensagem de login genérica + verify contra hash dummy (A05/A07); Pydantic v2 `extra="forbid"` em escrita (A03); query parametrizada SQLAlchemy, zero f-string em SQL (A03 FAIL-BLOCK).
- `br/lgpd-compliance` — **T-04, T-08, T-09**: PII de `users` (email, telefone, CPF, nome) marcada com comentário `# [LGPD]` no modelo; `cpf` armazenado para minimização e mascarado em serializers que não exigem o dado completo (`123.***.***-09`); colunas de anonimização (`deleted_at`, `anonymized_at`) e flags como **schema** nesta phase (jobs efetivos na Phase 14); PII nunca em log de aplicação (reforça denylist do config).
- `domain/mysql-schema-design` — **T-01, T-04, T-06**: naming convention `ix/uq/ck/fk/pk` herdada de `db/base.py`; `utf8mb4`/`utf8mb4_unicode_ci`; FK RESTRICT (DRV-002); `area_id BIGINT NOT NULL` + índice em tabelas de domínio via mixin; índices únicos para anti-duplicidade (email global; CPF por área via `uq` composto); trigger append-only via `op.execute()` (SQL puro proibido solto, specs); `DATETIME(6)` UTC.
- `domain/fastapi-production-patterns` — **T-08, T-09, T-10**: routers finos sob `/v1/auth/*` e `/v1/areas/*`; dependencies compostas (`get_current_user` → `area_scope` → `require_role`) sem lógica de autorização no corpo da rota; sessão async injetada via `Depends(get_session)`; erros via `AppError` (envelope RFC-7807-like da Phase 1), nunca stack trace no corpo.
- `product/api-design-contracts` — **T-05, T-08, T-09**: contratos Pydantic v2 explícitos (`LoginBody`, `TokenPair`, `RefreshBody`, `AreaCreate`, `AreaRead`) com `extra="forbid"`; `/v1/` versionado (DRV-003); idempotência por header em escrita relevante de área; códigos de erro estáveis e tipados (não vazam internals); contrato de `TokenPair` define o shape consumido pela UI da Phase 3.
- `quality/senior-quality-bar` (Gate 8) — **TODAS as tasks**: phase com código + auth → FAIL-BLOCK explicitamente vigiados nesta phase: (a) **segredo no repo** → `JWT_SECRET` só via env, `.env.example` com placeholder, nunca valor real commitado (T-02); (b) **auth indefinida** → todo endpoint de domínio passa por dependency de autorização explícita, nada de rota sem decisão de auth (T-10); (c) **PII em log** → eventos de auth e logs de request sem senha/token/email/cpf, reforçado por teste (T-08); (d) **injection** → SQL só via ORM parametrizado, zero f-string em SQL (T-04/T-06); (e) **N+1 em lista** → `list_for_area` evita N+1 (sem lazy-load em loop). Critério de fechamento: zero FAIL-BLOCK aberto contra `quality/senior-quality-bar`.

## Skills Dispensadas (com justificativa)

- **Matriz UI (`ui-ux-pro-max`, `accessibility-pro`, `component-library-governance`, `design-tokens-system`, `empty-states-polish`, `dark-mode-theming`, etc.)** — `has_ui: false` no ROADMAP Phase 2. Esta phase é backend-only (auth + multi-área + RBAC); a UI de login é escopo da Phase 3. Nenhum componente, token ou tela é produzido aqui.
- `br/brazilian-forms` (CNPJ/CPF/telefone) — não há formulários nesta phase. A validação de CPF/CNPJ de cadastro de loja/entregador é da Phase 4/5. Aqui `cpf` em `users` é apenas coluna/PII marcada e índice de unicidade; sem máscaras de input nem validação de formulário.
- `mobile/*` (`offline-first`, `push-notifications-architecture`, `gesture-touch-patterns`) — `mobile: false`; nenhum código de app/Capacitor/Ionic nesta phase.
- `domain/saas-billing-canonical` / `safe2pay-escrow-br` / `payment-checkout-ux` — `has_payments: false`. Nenhuma lógica de billing/assinatura/cobrança; planos e Safe2Pay entram nas Phases 10/11. (CLAUDE.md §18 avaliado e dispensado por escopo.)
- `quality/error-ux-patterns` — **avaliado e dispensado**: sem UI nesta phase. Mensagens de erro são da camada API (envelope RFC-7807-like + mensagem anti-enumeração), tratadas por `owasp-security`, não por error UX visual.
- **Integration contracts (`gsd-integration-checker`)** — **avaliado e dispensado**: `integration_check: false` no ROADMAP Phase 2. Não há contrato cross-layer cliente↔servidor a validar (sem frontend). Os contratos Pydantic ficam preparados para a Phase 3 consumir.

---

## Tech debt deste plano (verificação obrigatória v0.8+)

Consultado `.planning/TECH-DEBT.md` filtrando TDs com prazo/gatilho nesta phase:

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime — risco recorrente | **Prazo inclui Phase 2** explicitamente; `exp` do JWT e janelas de lockout são datetimes — risco direto. Toda data aware UTC (`datetime.now(UTC)`); ruff `DTZ` + AST guard ativos | T-02, T-05 (e teste em T-13) |
| TD-013 | Taxas sem versionamento temporal | `pre_launch_medium`, "Phase 10 decide". **Não entra**: nenhuma taxa/plano nesta phase; revisitar na Phase 10 | — (deferido, justificado) |
| TD-001..TD-009, TD-011, TD-012 | (sharding, KYC, OTP, score, APK, etc.) | Fora de escopo desta phase (auth/multi-área); prazos/gatilhos pós-M1 ou outras phases | — |

---

## Open questions / LOW confidence do RESEARCH (Regra 12)

Cada item LOW do RESEARCH vira **task explícita** (nenhum vira TD silenciosa):

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| **LOW-1** — Parâmetros exatos de argon2id (specs diz "custo 12", terminologia de bcrypt — **não aplicar literalmente**) | LOW | **Task T-02**: fixar `PasswordHasher` com parâmetros OWASP explícitos (`time_cost=2, memory_cost=19456, parallelism=1`), pinados no código; benchmark de verify ~100ms no hardware-alvo registrado em teste (`tests/test_security_argon2.py`); `check_needs_rehash` para upgrade futuro. Critério de aceite: parâmetros explícitos + teste de tempo. |
| **LOW-2** — Escolha final de lib JWT (PyJWT vs python-jose) | MEDIUM-LOW | **Task T-03**: fixar **PyJWT** em `pyproject.toml`; `algorithms=["HS256"]` pinado no decode; nota inline + linha no PLAN de que migração a RS256 (multi-validador, ex.: Menu Certo) seria **ADR futura**, não bloqueio agora. |
| **LOW-3** — Sintaxe de trigger append-only em dev (SQLite) vs CI/prod (MySQL) | MEDIUM | **Task T-12 + T-13**: a migration emite trigger MySQL-específica via `op.execute()` com guarda de dialeto (`if bind.dialect.name == "mysql"`); o teste de append-only roda **contra MySQL 8 no CI** (job de teste sobe MySQL, não só SQLite). Se o CI não subir MySQL no fechamento da phase → **vira TD `pre_launch_high`** (critério de aceite do ROADMAP depende disso) — registrar em TECH-DEBT.md nesse caso. |

---

## Threat model

Herdado da seção `## Security Baseline` do `RESEARCH.md` (10 ameaças → mitigações concretas). **Obrigatório** (phase com auth/PII/risco).

| ID | Ameaça (STRIDE) | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|-----------------|-------|---------|------------|-----------|------|
| TH-01 | Força bruta / credential stuffing (Spoofing) | Repetição de login | Alto | Alto | Lockout 5/15min por conta (423/429); argon2id memory-hard; aware UTC nas janelas | T-05, T-13 |
| TH-02 | Roubo de token access/refresh (Spoofing/Tampering) | Vazamento de token | Alto | Médio | Access HS256 15min; refresh opaco SHA-256 em DB; rotação + reuso; cookie httpOnly+Secure / Secure Storage; `algorithms=["HS256"]` pinado | T-03, T-07, T-08 |
| TH-03 | Reuso de refresh comprometido (Spoofing) | Refresh já rotacionado reusado | Alto | Médio | Detecção de reuso → revoga **família** + novo login obrigatório | T-07, T-11 |
| TH-04 | Enumeração de conta (Information Disclosure, RN-011) | Mensagem/timing distintos | Médio | Alto | Mensagem única "Credenciais inválidas"; `argon2.verify` contra hash dummy quando user inexiste; colisão de cadastro genérica | T-05, T-08, T-10 |
| TH-05 | Escalonamento cross-área (Elevation, RN-001) | Admin área acessa outra área | Alto | Médio | `WHERE area_id` na query; admin área cross-área → 403; recurso de outra área → 404; `require_role` dependency | T-06, T-10, T-12 |
| TH-06 | Bypass do admin plataforma silencioso (Repudiation) | Admin plataforma sai do escopo sem rastro | Alto | Médio | Bypass SEMPRE grava `audit_log` com `cross_area_bypass`, ator, ts, IP | T-04, T-10, T-12 |
| TH-07 | SQL injection (Tampering) | Input malicioso em query | Alto | Baixo | SQLAlchemy parametrizado; zero f-string em SQL (FAIL-BLOCK); Pydantic v2 `extra="forbid"` | T-04, T-06, T-08 |
| TH-08 | TOTP replay (Spoofing) | Reapresentar código TOTP | Médio | Médio | `TOTP.verify(code, valid_window=1)`; persistir último código/janela aceito; segredo TOTP nunca exposto em API | T-02, T-09 |
| TH-09 | PII em log de aplicação (Information Disclosure, RN-021) | Log com senha/token/CPF | Alto | Médio | NUNCA logar senha/token/refresh/CPF/CNPJ/corpo de auth; denylist central da Phase 1; CPF mascarado em respostas | T-08, T-09 |
| TH-10 | Tampering do audit_log (Tampering/Repudiation, RN-012) | UPDATE/DELETE direto no banco | Alto | Baixo | Trigger MySQL `BEFORE UPDATE/DELETE` → `SIGNAL SQLSTATE '45000'`; garantia no banco; teste de aceite | T-12, T-13 |

**Decisões de segurança registradas (derivação obrigatória):**
- **Lockout 5/15min** — derivado de ADR-005 + OWASP A04 (inviabiliza brute force sem punir caps lock); não copiado, derivado.
- **Política de senha** — mínimo **10 caracteres**, sem regras de composição arbitrárias (NIST 800-63B / A07); validado em `LoginBody`/registro via Pydantic.
- **`JWT_SECRET`** — ≥256 bits, só via env (nunca no repo); rotação invalida tokens vivos (aceitável p/ access 15min); adicionado a `core/config.py` + `.env.example` (placeholder).

---

## Performance budget

Herdado de `.planning/config.json > performance_budget`. Esta phase é **backend-only** (sem frontend → métricas de UI N/A).

**Backend:**
- **Endpoints de auth (`/v1/auth/login`, `/refresh`):** o `argon2id.verify` (~100ms) é o custo dominante e **aceitável no login** (controle de segurança intencional, A02). É **CPU-bound e isolado ao path de login** — não pode aparecer em outros endpoints.
- **p95 dos demais endpoints (`/v1/areas/*`, `get_current_user`):** ≤ **200ms** (não inclui o custo argon2; o decode JWT é HMAC, ~sub-ms).
- **N+1 queries:** zero toleradas. `list_for_area` usa `WHERE area_id` com índice; sem lazy-load em loop.
- **Connection pooling:** herdado da Phase 1 (`pool_size=5, max_overflow=10`) — suficiente para a carga do piloto.
- **Slow query:** > 100ms logada WARNING (config `slow_query_threshold_ms`).

Ferramenta: pytest-benchmark no teste de argon2 (T-02) confirma ~100ms; Prometheus em prod (infra Phase 1).

---

## Observability checklist

Aplicando `quality/observability-production`. Esta phase **tem endpoints** (`/v1/auth/*`, `/v1/areas/*`):

- [ ] Todo endpoint novo loga: `request_id`, `user_id`, `endpoint`, `method`, `status_code`, `duration_ms` (middleware da Phase 1 já emite; `user_id` agora **preenchido** após autenticação).
- [ ] Eventos de auth auditados como log estruturado: `login_ok`, `login_fail`, `lockout`, `refresh_rotated`, `refresh_reuse_detected`, `totp_enrolled` — **sem PII** (sem email/cpf/senha/token nos campos).
- [ ] `user_id` preenchido no contexto após `get_current_user` resolver (substitui o `None` reservado na Phase 1).
- [ ] Erros 4xx → WARNING; 5xx → ERROR (envelope da Phase 1 já distingue).
- [ ] Zero PII em logs: senha (mesmo errada), token/refresh, CPF/CNPJ completo, corpo de request de auth — proibidos (denylist `pii_fields_forbidden_in_logs`); reforçado por teste (`tests/test_anti_enumeration.py` + assert de log limpo).
- [ ] Queries > 100ms logadas WARNING.
- [ ] `audit_log` é **tabela**, não log de aplicação — `write_audit` grava before/after/ator/IP no banco, não no structlog.

---

## Error UX checklist

`N/A — este plano é backend-only; não toca UI de erro.` (Mensagens da API seguem envelope RFC-7807-like + regra anti-enumeração, tratadas em `owasp-security`.)

---

## Integration contracts

`N/A — integration_check: false no ROADMAP Phase 2; este plano é single-layer (backend). Contratos Pydantic (TokenPair etc.) ficam preparados para a UI da Phase 3 consumir.`

---

## Tasks

Formato estruturado — cada task tem skills aplicadas e critério de sucesso isolado. `parallel-hint` conservador.

### T-01 — Mixin AreaScoped + base repository + skeleton de módulos

- **Type:** infra / migration-prep
- **Files:** `apps/api/app/db/mixins.py`, `apps/api/app/db/repository.py`, `apps/api/app/auth/__init__.py`, `apps/api/app/areas/__init__.py`, `apps/api/app/audit/__init__.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — `AreaScopedMixin` → `area_id BIGINT NOT NULL` + índice `ix_<table>_area_id` + FK RESTRICT para `areas`; `TimestampMixin` com `DATETIME(6)` UTC; naming convention herdada de `db/base.py`.
  - `meta/orchestration-decision-tree` — contratos primeiro: mixin e base repository definidos antes dos models que os consomem (interface-first).
- **Descrição:** Criar `AreaScopedMixin` (toda tabela de domínio herda; tabelas globais `users`/`audit_log` **não** herdam — D-05) e `AreaScopedRepository` base cujos `get_for_area`/`list_for_area` injetam estruturalmente `WHERE area_id = :scope` (Pattern 1 do RESEARCH — filtro na query, nunca em `if`). Criar pacotes `auth/`, `areas/`, `audit/`.
- **Success:** `from app.db.mixins import AreaScopedMixin` e `from app.db.repository import AreaScopedRepository` importam; base repository não expõe método de leitura de domínio sem `area_id`.
- **Estimate:** ~10% contexto
- **Depends on:** none

### T-02 — Core security: argon2id (params explícitos + benchmark) + TOTP helpers — resolve LOW-1

- **Type:** new module
- **Files:** `apps/api/app/core/security.py`, `apps/api/app/core/config.py`, `apps/api/tests/test_security_argon2.py`
- **Skills aplicadas:**
  - `owasp-security` — `PasswordHasher` argon2id; `secrets.token_urlsafe`/`compare_digest`; segredo TOTP nunca exposto.
  - `quality/senior-quality-bar` — `JWT_SECRET` só via env (`core/config.py` + `.env.example` placeholder), nunca valor no repo (FAIL-BLOCK segredo).
- **Descrição:** Adicionar a `Settings`: `jwt_secret: str` (sem default em prod; placeholder só em `.env.example`), `jwt_algorithm: Literal["HS256"] = "HS256"`, `access_token_minutes: int = 15`. Em `security.py`: `PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1)` **explícito** (LOW-1 — **não** usar "custo 12" do specs literalmente), `hash_password`/`verify_password` com `check_needs_rehash`; helpers TOTP via `pyotp` (`random_base32`, `verify(code, valid_window=1)`, `provisioning_uri`); hash dummy para anti-enumeração. Datetimes aware UTC (TD-010).
- **Success:** `tests/test_security_argon2.py` verde — verify correto/incorreto, `check_needs_rehash`, e **benchmark de verify ~100ms** (assert de faixa, ex.: 40–250ms tolerante a hardware) confirmando parâmetros dimensionados.
- **Estimate:** ~20% contexto
- **Depends on:** none

### T-03 — Core security: JWT HS256 (encode/decode pinado) + refresh opaco — resolve LOW-2

- **Type:** new module
- **Files:** `apps/api/app/core/security.py` (continuação), `apps/api/pyproject.toml`, `apps/api/tests/test_jwt.py`
- **Skills aplicadas:**
  - `owasp-security` — claims `sub, area_scope, role, iat, exp, iss, aud, jti`; decode com `algorithms=["HS256"]` pinado + `options={"require": [...]}` (anti `alg:none`); refresh opaco SHA-256 + `compare_digest`.
  - `product/api-design-contracts` — formato de claim estável e versionável.
- **Descrição:** `uv add "argon2-cffi>=25,<26" "pyjwt>=2.10,<3" "pyotp>=2.9,<3"` (LOW-2: **PyJWT** fixada). `encode_access(user_id, area_scope, role)` e `decode_access(token)` (Pattern 3); `new_refresh()` → `(raw, sha256_hex)` (Pattern 4). `exp`/`iat` aware UTC. Nota inline: migração a RS256 (multi-validador) = ADR futura.
- **Success:** `tests/test_jwt.py` verde — round-trip; token com `alg=none` rejeitado; token sem `exp`/`aud`/`iss` rejeitado; `exp` expirado rejeitado; refresh hash determinístico.
- **Estimate:** ~15% contexto
- **Depends on:** T-02 (mesmo arquivo `security.py`)

### T-04 — Models + audit service: User, RefreshToken, Area, AreaAdmin, AuditLog

- **Type:** new module
- **Files:** `apps/api/app/auth/models.py`, `apps/api/app/areas/models.py`, `apps/api/app/audit/models.py`, `apps/api/app/audit/service.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — `User` global (sem `area_id`); `Area` com `codename` único, configs locais, `deleted_at` (soft-archive); `AreaAdmin` herda `AreaScopedMixin` (papel owner/manager/viewer); `RefreshToken` com hash, `rotated_at`, família; `AuditLog` global com `before`/`after` JSON, `actor_user_id`, `ip`, `cross_area_bypass`, `created_at`; FK RESTRICT, utf8mb4.
  - `br/lgpd-compliance` — PII de `User` (email, telefone, cpf, nome) com comentário `# [LGPD]`; colunas `deleted_at`/`anonymized_at` como **schema/flags** (jobs na Phase 14).
  - `owasp-security` — `write_audit` parametrizado (sem f-string); grava bypass não-silencioso (RN-001).
- **Descrição:** SQLAlchemy 2.0 `Mapped[]`. Lockout fields em `User`: `failed_attempts`, `first_failed_at`, `locked_until` (aware UTC). TOTP: `totp_secret` (nullable), `totp_required` flag. `write_audit(session, *, actor_id, action, area_id, before, after, ip, cross_area_bypass=False)`.
- **Success:** `python -c "from app.auth.models import User, RefreshToken; from app.areas.models import Area, AreaAdmin; from app.audit.models import AuditLog"` importa sem erro; PII marcada; `AuditLog` é global (sem mixin de área).
- **Estimate:** ~25% contexto
- **Depends on:** T-01

### T-05 — Auth service: login + lockout (aware UTC) + anti-enumeração

- **Type:** new module
- **Files:** `apps/api/app/auth/service.py`, `apps/api/app/auth/schemas.py`
- **Skills aplicadas:**
  - `owasp-security` — lockout 5/15min (A04/A07); verify contra hash dummy quando user inexiste (tempo constante, A05/A07); mensagem única "Credenciais inválidas".
  - `product/api-design-contracts` — `LoginBody`(email, password, totp opcional) / `TokenPair`(access, refresh, expires_in) Pydantic v2 `extra="forbid"`; senha mín. 10 chars (NIST/A07).
  - `quality/observability-production` — emite `login_ok`/`login_fail`/`lockout` sem PII.
- **Descrição:** `authenticate(email, password, totp)`: checa `is_locked` (aware UTC, TD-010) → 423; `register_failed_attempt` na falha; verify argon2; TOTP se exigido; sucesso → emite `TokenPair` + persiste refresh. Lockout exatamente como Code Example do RESEARCH.
- **Success:** lógica coberta por T-13 (lockout) e T-14 (flow/anti-enum); schemas com `extra="forbid"` e mínimo de senha.
- **Estimate:** ~25% contexto
- **Depends on:** T-02, T-03, T-04

### T-06 — Areas service + RBAC role resolution

- **Type:** new module
- **Files:** `apps/api/app/areas/service.py`, `apps/api/app/areas/schemas.py`
- **Skills aplicadas:**
  - `owasp-security` — CRUD de área só para admin plataforma; `WHERE area_id` via base repository; 404 cross-área.
  - `domain/mysql-schema-design` — soft-archive (não deletar com dependentes → orientar arquivamento, REQ-002); query parametrizada.
  - `product/api-design-contracts` — `AreaCreate`/`AreaRead`/`AreaUpdate` Pydantic v2 `extra="forbid"`; idempotência por header em create.
- **Descrição:** `create_area`/`get_area`/`list_areas`/`archive_area`; `resolve_role(user, area_id)` consulta `area_admins` (nesta phase só este vínculo; merchant_users/couriers em phases futuras) e retorna papel naquela área (D-09). Tentativa de deletar área com dependentes → `AppError` orientando arquivamento.
- **Success:** coberto por T-12 (isolamento) e T-15 (RBAC matrix); `resolve_role` retorna papel correto por contexto de área.
- **Estimate:** ~20% contexto
- **Depends on:** T-01, T-04

### T-07 — Refresh service: rotação + detecção de reuso (revoga família)

- **Type:** new module
- **Files:** `apps/api/app/auth/service.py` (continuação)
- **Skills aplicadas:**
  - `owasp-security` — refresh já rotacionado reusado = sessão comprometida → revogar família inteira (A02); `compare_digest`.
  - `quality/observability-production` — emite `refresh_rotated` / `refresh_reuse_detected`.
- **Descrição:** `rotate_refresh(raw)`: localiza por SHA-256; se `rotated_at` já preenchido → reuso → revoga todos os refresh da família (mesmo user/device) + exige novo login; senão rotaciona (marca `rotated_at`, emite novo par). `logout(raw)` revoga.
- **Success:** coberto por T-14 (flow): refresh rotaciona; reuso revoga família.
- **Estimate:** ~15% contexto
- **Depends on:** T-05

### T-08 — Auth router: /v1/auth/login, /refresh, /logout

- **Type:** new_endpoint
- **Files:** `apps/api/app/auth/router.py`, `apps/api/app/api/v1/router.py`
- **Skills aplicadas:**
  - `domain/fastapi-production-patterns` — router fino; sessão via `Depends(get_session)`; erros via `AppError`.
  - `owasp-security` — refresh em cookie httpOnly+Secure (web); resposta de erro genérica; sem stack trace.
  - `quality/observability-production` — 6 campos de log; `user_id` preenchido; eventos auth sem PII.
  - `br/lgpd-compliance` — nenhuma PII no corpo de log; corpo de request de auth nunca logado.
- **Descrição:** Endpoints sob `/v1/auth/*`; `login` retorna `TokenPair` (access no body, refresh em cookie httpOnly+Secure + também no body para app); `refresh` rotaciona; `logout` revoga. Registrar `auth.router` no `api_router`.
- **Success:** `curl -X POST /v1/auth/login` com seed válido → 200 + access + refresh cookie; inválido → 401 genérico (verificado em T-14).
- **Estimate:** ~20% contexto
- **Depends on:** T-05, T-07

### T-09 — Auth dependencies (get_current_user, area_scope, require_role) + TOTP enroll endpoint

- **Type:** new module + endpoint
- **Files:** `apps/api/app/auth/dependencies.py`, `apps/api/app/auth/router.py` (continuação)
- **Skills aplicadas:**
  - `owasp-security` — `get_current_user` decode pinado; `area_scope` resolve escopo do token + path, cross-área de admin de área → 403; `require_role`/`require_platform_admin` dependency separada (A01, nunca `if user.is_admin`).
  - `domain/fastapi-production-patterns` — dependencies compostas em cadeia, sem lógica de auth no corpo da rota.
  - `quality/observability-production` — preenche `user_id` no contexto de log após resolver usuário.
  - `br/lgpd-compliance` — endpoint de TOTP nunca devolve o segredo após enroll (só provisioning URI uma vez).
- **Descrição:** Cadeia `get_current_user` → `area_scope(user, path/token)` → `require_role(*allowed)`; `require_platform_admin`. Admin plataforma sem TOTP → forçado a configurar (`/v1/auth/totp/enroll` + verify) no primeiro login (REQ-005). TOTP `valid_window=1`, anti-replay (último código aceito).
- **Success:** coberto por T-12/T-15/T-16; admin plataforma sem TOTP bloqueado até enroll (T-16).
- **Estimate:** ~25% contexto
- **Depends on:** T-03, T-06, T-08

### T-10 — Areas router: /v1/areas (CRUD restrito a admin plataforma) + bypass auditado

- **Type:** new_endpoint
- **Files:** `apps/api/app/areas/router.py`, `apps/api/app/api/v1/router.py` (continuação)
- **Skills aplicadas:**
  - `owasp-security` — CRUD atrás de `require_platform_admin`; recurso de outra área → 404; admin de área cross-área → 403; bypass do admin plataforma grava `audit_log` (RN-001, não silencioso).
  - `domain/fastapi-production-patterns` — router fino; dependencies de autorização explícitas (nenhuma rota sem decisão de auth — Gate 8).
  - `product/api-design-contracts` — `/v1/` versionado; idempotência por header em create.
- **Descrição:** `POST/GET/PATCH/POST(archive) /v1/areas`; admin plataforma com `area_scope=None` opera cross-área e CADA acesso cross-área grava `write_audit(..., cross_area_bypass=True)`. Registrar `areas.router`.
- **Success:** coberto por T-12 (isolamento + bypass auditado); toda rota tem dependency de auth (zero rota órfã).
- **Estimate:** ~20% contexto
- **Depends on:** T-06, T-09

### T-11 — Migration 0002: areas, users, area_admins, refresh_tokens, audit_log + triggers — parte schema

- **Type:** migration
- **Files:** `apps/api/alembic/versions/0002_core_auth_multiarea.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — tabelas com `utf8mb4`/naming convention herdada; `area_id NOT NULL`+índice em `area_admins`; índices únicos anti-duplicidade (REQ-006: email global único; CPF único por área via `uq` composto `(area_id?, cpf)` — CPF global em `users` + unicidade de vínculo por área tratada quando `couriers` chegar; nesta phase email/cpf únicos em `users`); FK RESTRICT (DRV-002); `DATETIME(6)`.
  - `owasp-security` — `refresh_tokens.token_hash` único; nenhum segredo em claro no schema.
- **Descrição:** `upgrade()` cria as 5 tabelas via `op.create_table` (não SQL solto). `down_revision = "0001_baseline"`. `downgrade()` dropa tabelas (triggers dropados em T-12 antes). Anti-duplicidade: `uq_users_email`, `uq_users_cpf` (mensagem genérica fica no service, T-05).
- **Success:** `cd apps/api && uv run alembic upgrade head` e `alembic downgrade -1` limpos contra MySQL; tabelas com utf8mb4.
- **Estimate:** ~20% contexto
- **Depends on:** T-04

### T-12 — Migration 0002: triggers append-only (op.execute, guarda de dialeto) — resolve LOW-3 (parte migration)

- **Type:** migration
- **Files:** `apps/api/alembic/versions/0002_core_auth_multiarea.py` (continuação)
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — trigger MySQL via `op.execute()` (SQL puro solto proibido pelas specs); `BEFORE UPDATE`/`BEFORE DELETE` → `SIGNAL SQLSTATE '45000'` (RN-012).
  - `owasp-security` — imutabilidade garantida no banco, não em convenção (A08).
- **Descrição:** Dentro de `upgrade()`, após criar `audit_log`: `if op.get_bind().dialect.name == "mysql"` → `op.execute(CREATE TRIGGER trg_audit_log_no_update ...)` e `..._no_delete ...` (LOW-3: guarda de dialeto; SQLite não recebe o mesmo SQL). `downgrade()`: `DROP TRIGGER IF EXISTS` antes de dropar a tabela.
- **Success:** trigger criada em MySQL; downgrade dropa trigger antes da tabela sem erro.
- **Estimate:** ~10% contexto
- **Depends on:** T-11

### T-13 — Testes Wave 0 + fixtures + lockout (aware UTC)

- **Type:** test
- **Files:** `apps/api/tests/conftest.py` (extensão), `apps/api/tests/test_auth_lockout.py`, `apps/api/tests/test_totp.py`
- **Skills aplicadas:**
  - `owasp-security` — assert 423/429 na 6ª tentativa em 15 min; TOTP replay recusado.
  - `quality/senior-quality-bar` — teste confirma datetimes aware UTC (sem `TypeError` naive/aware — TD-010).
- **Descrição:** Estender `conftest.py`: fixtures de sessão async, seed de 2 áreas + 2 `area_admins`, factory de user, admin plataforma. `test_auth_lockout`: 6ª tentativa → 423/429; janela aware UTC. `test_totp`: admin plataforma sem TOTP → forçado a configurar; replay recusado.
- **Success:** `uv run pytest tests/test_auth_lockout.py tests/test_totp.py -x` exit 0. **Critério de aceite ROADMAP (lockout).**
- **Estimate:** ~20% contexto
- **Depends on:** T-05, T-09

### T-14 — Testes auth flow + anti-enumeração

- **Type:** test
- **Files:** `apps/api/tests/test_auth_flow.py`, `apps/api/tests/test_anti_enumeration.py`
- **Skills aplicadas:**
  - `owasp-security` — login feliz; refresh rotaciona; reuso revoga família; mensagem genérica + timing equivalente.
  - `quality/observability-production` — assert de que log de login não contém PII (email/senha/token).
- **Descrição:** `test_auth_flow`: login → access+refresh; rotação; reuso → 401 + família revogada. `test_anti_enumeration`: e-mail inexistente vs senha errada → mesma mensagem; colisão de cadastro não revela qual dado; verify roda mesmo sem user.
- **Success:** `uv run pytest tests/test_auth_flow.py tests/test_anti_enumeration.py -x` exit 0.
- **Estimate:** ~20% contexto
- **Depends on:** T-08, T-07

### T-15 — Teste de isolamento multi-área + bypass auditado

- **Type:** test
- **Files:** `apps/api/tests/test_area_isolation.py`, `apps/api/tests/test_rbac_matrix.py`
- **Skills aplicadas:**
  - `owasp-security` — admin área cross-área → 403; recurso de outra área → 404; matriz de papéis (operador/viewer sem permissão → 403); `require_platform_admin` separada.
  - `quality/observability-production` — assert da linha em `audit_log` no bypass.
- **Descrição:** `test_area_isolation`: seed 2 áreas; admin área A `GET /v1/areas/{B}` → 403; listagem scoped à A nunca traz linha de B; `test_platform_bypass_audited`: admin plataforma → 200 + linha `audit_log` com `cross_area_bypass=True`. `test_rbac_matrix`: cada papel testado por endpoint.
- **Success:** `uv run pytest tests/test_area_isolation.py tests/test_rbac_matrix.py -x` exit 0. **Critério de aceite ROADMAP (isolamento).**
- **Estimate:** ~25% contexto
- **Depends on:** T-10, T-12

### T-16 — Teste de trigger append-only contra MySQL (CI) — resolve LOW-3 (parte teste)

- **Type:** test
- **Files:** `apps/api/tests/test_audit_append_only.py`
- **Skills aplicadas:**
  - `owasp-security` — imutabilidade verificada no banco (A08).
  - `domain/mysql-schema-design` — teste assume MySQL 8 (trigger `SIGNAL`); marcado para rodar no job MySQL do CI.
- **Descrição:** Aplica migration; INSERT em `audit_log` OK; `UPDATE` → erro MySQL (SQLSTATE 45000); `DELETE` → erro. **Marca `@pytest.mark.mysql`** (skip se não-MySQL) e o CI **deve** subir MySQL 8 para este teste. **LOW-3:** se o CI não rodar contra MySQL no fechamento da phase → registrar TD `pre_launch_high` em TECH-DEBT.md (critério de aceite do ROADMAP depende disso).
- **Success:** `uv run pytest tests/test_audit_append_only.py -x` exit 0 **contra MySQL real**. **Critério de aceite ROADMAP (trigger).**
- **Estimate:** ~15% contexto
- **Depends on:** T-12

---

## Execution order

Waves (grupos paralelizáveis; `parallel-hint` conservador — tasks que compartilham `core/security.py` ou `service.py` ficam sequenciais no mesmo módulo):

- **Wave 1 (paralelo):** T-01 (db mixins/repo), T-02 (security: argon2/TOTP + config) — módulos distintos, sem dependência.
- **Wave 2:** T-03 (security: JWT/refresh — depende T-02, mesmo arquivo), T-04 (models + audit — depende T-01).
- **Wave 3:** T-05 (auth service login/lockout — depende T-02/T-03/T-04), T-06 (areas service + RBAC resolve — depende T-01/T-04), T-11 (migration schema — depende T-04). *Paralelizáveis: módulos distintos.*
- **Wave 4:** T-07 (refresh rotação — depende T-05), T-12 (migration triggers — depende T-11).
- **Wave 5:** T-08 (auth router — depende T-05/T-07).
- **Wave 6:** T-09 (auth dependencies + TOTP enroll — depende T-03/T-06/T-08).
- **Wave 7:** T-10 (areas router + bypass auditado — depende T-06/T-09).
- **Wave 8 (testes de aceite, paralelo):** T-13 (lockout/TOTP — depende T-05/T-09), T-14 (flow/anti-enum — depende T-08/T-07), T-15 (isolamento/RBAC — depende T-10/T-12), T-16 (trigger MySQL — depende T-12).

Commit atômico por wave: `feat(phase-2): <wave summary>`.

---

## Reconciliation expectations

Ao fim da execução, o `/gsd:reconcile-state 2` verifica:

- Todos os arquivos de `files` de cada task existem.
- Endpoints declarados (`/v1/auth/login|refresh|logout|totp/enroll`, `/v1/areas` CRUD) têm handler implementado e dependency de auth.
- Skills citadas de fato aplicadas: `WHERE area_id` presente no base repository (não em `if`); `algorithms=["HS256"]` pinado no decode; argon2id com params explícitos; trigger append-only via `op.execute`; bypass grava audit_log.
- LOW-1/2/3 resolvidos como tasks (não viraram TD silenciosa); se CI não subiu MySQL → TD `pre_launch_high` registrada (LOW-3).
- Nenhum arquivo-fantasma; nenhuma feature-fantasma (código sem task — ex.: nada de billing/UI/entrega).

Divergências entram em `RECONCILIATION.md` antes de fechar a fase.

---

## Rollback plan

- Revert do(s) commit(s) `feat(phase-2): ...`.
- Migrations: `cd apps/api && uv run alembic downgrade 0001_baseline` (dropa triggers antes das tabelas — T-12 garante ordem).
- Sem ação de ops externa (sem serviço externo nesta phase); `JWT_SECRET` permanece só em env.

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
