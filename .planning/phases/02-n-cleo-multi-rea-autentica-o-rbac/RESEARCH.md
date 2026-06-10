# Phase 2: Núcleo multi-área + autenticação + RBAC — Research

**Researched:** 2026-06-10
**Domain:** Identidade, autenticação, autorização multi-tenant (área) e infraestrutura append-only sobre FastAPI 0.115 + SQLAlchemy 2.0 + MySQL 8
**Confidence:** HIGH (stack e padrões) / MEDIUM (parâmetros exatos de argon2id, escolha fina de lib JWT)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (travadas por ADR-001 / ADR-005)
- **D-01:** JWT **HS256**, access token **15 min** (stateless, em memória no cliente). Refresh token **opaco** persistido em DB (não-JWT), rotacionável. Web: refresh em cookie httpOnly+Secure; app: Secure Storage. [VERIFIED: ADR-005]
- **D-02:** Hash de senha com **argon2id** (parâmetros recomendados OWASP). Nunca bcrypt. [VERIFIED: ADR-005]
- **D-03:** **TOTP** obrigatório para admin de plataforma; opt-in para os demais papéis. [VERIFIED: ADR-005]
- **D-04:** Lockout de **5 tentativas / 15 min** por conta; resposta 423/429. Anti-enumeração: erros que não revelam se e-mail existe. [VERIFIED: ADR-005 + RN-011]
- **D-05:** `area_id` obrigatório em TODA tabela de domínio; globais = exatamente `users`, `audit_log`, `ai_usage_log`. [VERIFIED: ADR-001]
- **D-06:** Middleware injeta o escopo de área do token; toda query de domínio filtra por área. Admin de plataforma bypassa com **flag auditada**. Cross-área de admin de área → **403**. [VERIFIED: ADR-001/RN-001]
- **D-07:** Teste de isolamento obrigatório (seed 2+ áreas, query cross-área → 403/vazio) — critério de aceite da phase. [VERIFIED: ROADMAP]
- **D-08:** 6 papéis: admin_plataforma, admin_area (owner/manager/viewer), loja_dono, loja_operador, entregador, destinatário (sem login). Permissões por papel checadas em dependency FastAPI. Nesta phase só `users` + `areas` + `area_admins`. [VERIFIED: visao-geral.md]
- **D-09:** Um `user` pode ter múltiplos vínculos; RBAC resolve papel por contexto de área. [VERIFIED: entidades.md]
- **D-10:** `audit_log` e tabelas de transição **INSERT-only via trigger** MySQL. Teste: UPDATE em audit_log → erro MySQL. [VERIFIED: RN-012]
- **D-11:** Ações administrativas sensíveis gravam before/after no audit_log com ator, timestamp, IP. [VERIFIED: RN-012]
- **D-12:** PII de `users` marcada; CPF mascarado em telas que não exigem o dado completo; PII nunca em log. Hooks de anonimização como schema/flags aqui; jobs efetivos na Phase 14. [VERIFIED: RN-021]

### Claude's Discretion
- Estrutura interna dos módulos (`app/auth/`, `app/areas/`, `app/core/security.py`).
- Biblioteca TOTP (ex.: `pyotp`) e de JWT (ex.: `pyjwt` / `python-jose`) — escolher na pesquisa.
- Formato exato do payload do JWT (claims: sub, area_scope, role, exp, jti).

### Deferred Ideas (OUT OF SCOPE)
- Cadastro/onboarding de loja (F-01) — Phase 4.
- Cadastro/KYC de entregador (F-02) — Phase 5.
- UI de login (tela 01) — Phase 3.
- Jobs de anonimização LGPD efetivos — Phase 14.
- Entidades de domínio (merchants, couriers, deliveries) — phases respectivas.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-001 | Multi-área shared-DB com `area_id` em tudo; middleware injeta escopo; cross-área → 403; bypass admin auditado | §Multi-área isolation patterns (mixin AreaScoped, dependency `area_scope`, scoped repository, teste 2 áreas) |
| REQ-002 | Entidade Área com regras locais configuráveis; CRUD restrito ao admin plataforma; não deletável com entregas (arquivamento) | §Abordagem técnica → modelo `areas` (codename único, soft-archive); RBAC dependency `require_platform_admin` |
| REQ-004 | Audit log + transições append-only (trigger nega UPDATE/DELETE; before/after; ator/ts/IP) | §Append-only via trigger MySQL; §Don't Hand-Roll (não validar imutabilidade só em app) |
| REQ-005 | JWT HS256 15min + refresh opaco em DB + argon2id + TOTP + lockout 5/15min | §Abordagem por área → Auth completa; §Security Baseline ameaças 1–3, 6 |
| REQ-006 | Anti-duplicidade (CNPJ/CPF+telefone+e-mail únicos por tipo); mensagem que não revela QUAL dado colide; CPF por área | §Security Baseline ameaça 4 (enumeração); índices únicos parciais; resposta genérica |
| REQ-007 | 6 papéis; matriz de permissões por endpoint; operador sem financeiro; admin de área não vê outras áreas (403) | §RBAC via dependencies FastAPI; matriz de permissões; §Security Baseline ameaça 5 |
</phase_requirements>

## Summary

Esta phase constrói a fundação de identidade da plataforma sobre o skeleton já entregue na Phase 1 (FastAPI factory, sessão async SQLAlchemy 2.0/aiomysql, structlog, error envelope, request-context middleware com `user_id=None` já reservado). O trabalho se divide em quatro frentes: (1) **modelos + migrations Alembic** das três tabelas desta phase — `areas`, `users` (global), `area_admins` — mais `audit_log` (global) com trigger append-only; (2) **autenticação** — argon2id via `argon2-cffi`, JWT HS256 de acesso (15 min) via `PyJWT`, refresh opaco com hash em DB e rotação com detecção de reuso, TOTP via `pyotp`, e lockout 5/15min; (3) **isolamento multi-área** — como MySQL 8 **não tem Row-Level Security nativo**, o isolamento é implementado na **camada de aplicação** via um `area_scope` resolvido no token, injetado por dependency FastAPI, aplicado como `WHERE area_id = :area_id` em todo repositório de domínio (padrão "tenant_id na query, nunca em if"); (4) **RBAC** dos 6 papéis via dependencies FastAPI compostas (`get_current_user` → `require_role(...)` → `require_area_scope`).

A escolha de **HS256 está travada por ADR-005** e é a correta para o cenário atual (um único processo FastAPI emite E valida o token — OWASP A02 tabela de decisão). Caso a validação passe a ser feita por mais de um processo (gateway, worker), a migração para RS256/ES256 deve virar ADR — fica registrado como nota, não como bloqueio.

**Primary recommendation:** `argon2-cffi` (PasswordHasher com defaults atuais ≈ OWASP) + `PyJWT` (HS256, claims pinadas) + refresh opaco `secrets.token_urlsafe(32)` hasheado com SHA-256 em DB + `pyotp` (TOTP RFC 6238); isolamento de área via mixin `AreaScoped` + dependency `area_scope` + base repository que aplica o filtro estruturalmente; append-only via trigger MySQL `BEFORE UPDATE`/`BEFORE DELETE` que faz `SIGNAL SQLSTATE '45000'`. Todos os datetimes (`exp`, janelas de lockout) **aware UTC** (`datetime.now(UTC)`) — risco direto de TD-010.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Hash/verify de senha (argon2id) | API / Backend | — | Segredo nunca sai do servidor; cálculo CPU-bound controlado pelo servidor |
| Emissão/validação de JWT access | API / Backend | — | HS256: o mesmo processo emite e valida; segredo só no servidor |
| Armazenamento de refresh token | Database (hash) + Cliente (valor) | API | Valor opaco no cliente (cookie httpOnly / Secure Storage); só o hash em DB |
| TOTP enroll/verify | API / Backend | Cliente (app autenticador) | Segredo TOTP gerado e validado server-side; cliente só digita o código |
| Lockout / rate limit de login | API / Backend | Redis (opcional p/ contadores) | Invariante de segurança no servidor; nunca no cliente |
| Escopo de área (multi-tenant) | API / Backend (query) | Database (FK + índice) | "WHERE area_id" estrutural na query; FK garante integridade |
| RBAC (decisão de papel) | API / Backend (dependency) | — | Autoridade de autorização é sempre o servidor; UI esconde, não autoriza |
| Imutabilidade do audit_log | Database (trigger) | API (insert) | Trigger é a garantia real; app só escreve |
| Mascaramento de CPF em resposta | API / Backend (serializer) | Cliente (apresentação) | PII reduzida na borda do servidor; nunca confiar só no front |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `argon2-cffi` | 25.1.0 | Hash de senha argon2id (`PasswordHasher`) | [VERIFIED: PyPI 2026-06-10] Binding de referência do vencedor do Password Hashing Competition; `PasswordHasher` traz defaults atualizados ≈ OWASP, `check_needs_rehash` para upgrade transparente de parâmetros. [CITED: github.com/hynek/argon2-cffi] |
| `PyJWT` | 2.13.0 | Encode/decode do JWT access HS256 | [VERIFIED: PyPI 2026-06-10] Lib JWT mais simples e ativa em Python; suporta pin de algoritmo e `options={"require": [...]}` no decode (mitiga `alg:none`). Preferida a `python-jose`, que tem manutenção irregular e CVEs históricos — ver Alternativas. |
| `pyotp` | 2.9.0 | TOTP RFC 6238 (enroll + verify + provisioning URI) | [VERIFIED: PyPI 2026-06-10] Implementação canônica de TOTP/HOTP em Python; `pyotp.random_base32()`, `TOTP.verify(code, valid_window=1)`, `provisioning_uri()` para QR. |
| `SQLAlchemy` | 2.0.x (já instalado) | Modelos + queries parametrizadas (anti-injection) | [VERIFIED: pyproject.toml] Já é o ORM do projeto; toda query parametrizada por padrão (OWASP A03). |
| `alembic` | 1.13.x (já instalado) | Migrations das tabelas + trigger append-only | [VERIFIED: pyproject.toml] Já configurado na Phase 1; SQL puro não aceito (specs/stack.yaml) — trigger entra via `op.execute()` na migration. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `secrets` (stdlib) | py3.13 | Geração de refresh token opaco (`token_urlsafe(32)`) e `compare_digest` em comparações de token/HMAC | Sempre que gerar valor aleatório de segurança ou comparar segredo (timing-safe) |
| `hashlib` (stdlib) | py3.13 | SHA-256 do refresh token antes de persistir | Hash do refresh opaco no DB (RN-020 usa o mesmo padrão para API keys nas phases futuras) |
| `redis` | 5.x (já instalado) | (Opcional) contador de lockout/rate-limit sliding window | Se o lockout precisar de granularidade por-IP além de por-conta; senão coluna em `users` basta no M1 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `PyJWT` | `python-jose[cryptography]` | python-jose suporta JWE e mais algoritmos, mas manutenção irregular e CVEs (ex.: confusão de algoritmo). Para HS256 simples, PyJWT é mais enxuto e seguro por default. **Recomendação: PyJWT.** |
| `argon2-cffi` defaults | parâmetros OWASP explícitos (`PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)`) | Defaults da lib evoluem e podem divergir do alvo OWASP exato em uma versão. **Recomendação: setar parâmetros explícitos no PLAN** (ver LOW-1) para reprodutibilidade entre máquinas/versões. |
| Lockout em coluna no DB | Lockout em Redis (sliding window) | Redis dá rate-limit por IP global e expira sozinho; coluna no DB é mais simples e auditável e basta para 5/15min por conta no piloto. **Recomendação: coluna no DB no M1; Redis se surgir necessidade por-IP.** |
| Trigger MySQL append-only | Apenas convenção de app (sem UPDATE/DELETE no código) | Convenção é esquecível e não resiste a acesso direto ao banco. RN-012 exige garantia no banco. **Recomendação: trigger (obrigatória).** |

**Installation:**
```bash
# em apps/api — adicionar ao pyproject.toml [project.dependencies]
uv add "argon2-cffi>=25,<26" "pyjwt>=2.10,<3" "pyotp>=2.9,<3"
```

**Version verification (2026-06-10, `pip index versions`):**
- `argon2-cffi`: 25.1.0 (latest) — [VERIFIED]
- `PyJWT`: 2.13.0 (latest) — [VERIFIED]
- `pyotp`: 2.9.0 (latest) — [VERIFIED]

> Nota: `cryptography>=43` já está no pyproject (handshake MySQL caching_sha2_password). PyJWT HS256 não precisa de `cryptography` (só HMAC stdlib), mas a presença não atrapalha.

## Architecture Patterns

### System Architecture Diagram

```
                          ┌─────────────────────────────────────────────┐
   POST /v1/auth/login    │                  FastAPI app                  │
   {email,password,totp}  │                                              │
   ───────────────────────▶ RequestContextMiddleware (Phase 1)          │
                          │   binds request_id; user_id=None→preenchido  │
                          │            │                                  │
                          │            ▼                                  │
                          │   /v1/auth/login  ──┐                         │
                          │      1. lockout check (users.failed_attempts, │
                          │         locked_until — datetime aware UTC)    │
                          │      2. argon2.verify(hash, password)         │
                          │         (sempre roda mesmo se user inexiste — │
                          │          anti-enumeração, tempo constante)    │
                          │      3. se TOTP exigido: pyotp.verify(code)   │
                          │      4. emite access JWT(HS256, 15min) +       │
                          │         refresh opaco (token_urlsafe → sha256 │
                          │         em refresh_tokens)                    │
                          │            │                                  │
   access JWT + refresh   ◀────────────┘  (refresh em cookie httpOnly web │
   ──────────────────────┐               / Secure Storage app)           │
                          │                                              │
   Authorization: Bearer │            ┌─────────────────────────────┐    │
   <access JWT>          ─┼────────────▶  Auth dependencies          │    │
   GET /v1/areas/{id}/... │            │  get_current_user           │    │
                          │            │   → decode JWT (pin HS256,   │    │
                          │            │     require exp/iss/aud/jti) │    │
                          │            │   → carrega User             │    │
                          │            │  area_scope(user, path/token)│    │
                          │            │  require_role(...)           │    │
                          │            └──────────┬──────────────────┘    │
                          │                       ▼                       │
                          │            Domain repository                 │
                          │            .get_for_area(id, area_id=scope)   │
                          │            → SELECT ... WHERE area_id=:scope  │
                          │            (404 se de outra área; 403 se      │
                          │             admin de área tenta outra área)   │
                          │                       │                       │
                          └───────────────────────┼───────────────────────┘
                                                  ▼
                          ┌──────────────────────────────────────────────┐
                          │ MySQL 8 (shared DB, area_id em tudo)          │
                          │  users(global) · areas · area_admins ·        │
                          │  refresh_tokens · audit_log(global)           │
                          │  ┌── trigger BEFORE UPDATE/DELETE em          │
                          │  │   audit_log → SIGNAL SQLSTATE '45000'      │
                          │  └── (append-only, RN-012)                    │
                          └──────────────────────────────────────────────┘
```

### Recommended Project Structure
```
apps/api/app/
├── core/
│   └── security.py        # argon2 PasswordHasher singleton, jwt encode/decode,
│                          #   refresh token gen+hash, TOTP helpers, compare_digest
├── auth/
│   ├── models.py          # User, RefreshToken (SQLAlchemy 2.0 Mapped[])
│   ├── schemas.py         # Pydantic v2: LoginBody, TokenPair, RefreshBody...
│   ├── service.py         # login/refresh/logout/lockout/totp-enroll (lógica)
│   ├── dependencies.py    # get_current_user, require_role, area_scope, require_platform_admin
│   └── router.py          # /v1/auth/* endpoints
├── areas/
│   ├── models.py          # Area, AreaAdmin
│   ├── schemas.py
│   ├── service.py
│   └── router.py          # /v1/areas/* (CRUD restrito a admin plataforma)
├── audit/
│   ├── models.py          # AuditLog (global, append-only)
│   └── service.py         # write_audit(actor, action, before, after, ip)
├── db/
│   ├── mixins.py          # AreaScopedMixin (area_id NOT NULL + índice), TimestampMixin
│   └── repository.py      # AreaScopedRepository base (.get_for_area / .list_for_area)
└── api/v1/router.py       # inclui auth.router, areas.router
```

### Pattern 1: Escopo de tenant na QUERY (não em `if`)
**What:** O `area_id` do escopo entra no `WHERE` de todo repositório de domínio, nunca em um `if` após o fetch.
**When to use:** Toda leitura/escrita de tabela com `area_id` (i.e., toda tabela de domínio).
**Example:**
```python
# Source: owasp-security SKILL.md §A01 (Ownership), adaptado ao domínio Jaxegô
# ✅ CERTO — escopo de área na query, 404 para recurso de outra área
async def get_area_resource_for_scope(session, resource_id: int, *, area_id: int):
    stmt = select(Resource).where(
        Resource.id == resource_id,
        Resource.area_id == area_id,   # estrutural, não esquecível
    )
    obj = (await session.execute(stmt)).scalar_one_or_none()
    if obj is None:
        raise NotFoundError()  # 404 — não vaza que o recurso existe em outra área
    return obj
```

### Pattern 2: argon2id com parâmetros explícitos e rehash transparente
**What:** PasswordHasher com parâmetros pinados; verificação dispara rehash quando os parâmetros sobem.
**When to use:** Hash no signup/troca de senha; verify no login.
**Example:**
```python
# Source: github.com/hynek/argon2-cffi README + docs/parameters.md [CITED]
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Parâmetros explícitos (ver LOW-1: confirmar alvo OWASP no PLAN)
ph = PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1)  # ~19 MiB

def hash_password(raw: str) -> str:
    return ph.hash(raw)

def verify_password(stored_hash: str, raw: str) -> tuple[bool, str | None]:
    try:
        ph.verify(stored_hash, raw)
    except VerifyMismatchError:
        return False, None
    new_hash = ph.hash(raw) if ph.check_needs_rehash(stored_hash) else None
    return True, new_hash  # persistir new_hash se != None
```

### Pattern 3: JWT HS256 com claims pinadas e algoritmo travado no decode
**What:** Encode com claims `sub, area_scope, role, exp, iat, iss, aud, jti`; decode com algoritmo pinado e claims obrigatórias.
**When to use:** Emissão no login/refresh; validação em `get_current_user`.
**Example:**
```python
# Source: owasp-security SKILL.md §A02 (JWT) [CITED]
import jwt
from datetime import datetime, timedelta, UTC
import uuid

def encode_access(user_id: int, area_scope: int | None, role: str) -> str:
    now = datetime.now(UTC)  # AWARE — TD-010
    payload = {
        "sub": str(user_id),
        "area_scope": area_scope,   # None p/ admin plataforma (bypass auditado)
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "iss": "jaxego",
        "aud": "jaxego-api",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_access(token: str) -> dict:
    return jwt.decode(
        token, settings.jwt_secret,
        algorithms=["HS256"],                          # PINADO — mitiga alg:none
        audience="jaxego-api", issuer="jaxego",
        options={"require": ["exp", "iss", "aud", "sub", "jti"]},
    )
```

### Pattern 4: Refresh opaco com rotação e detecção de reuso
**What:** Refresh = random 256-bit opaco; só o SHA-256 fica em DB; cada uso rotaciona; reuso de token já rotacionado revoga a família.
**When to use:** `/v1/auth/refresh`.
**Example:**
```python
# Source: owasp-security SKILL.md §A02 (Refresh tokens) [CITED]
import secrets, hashlib

def new_refresh() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)                    # 256 bits
    return raw, hashlib.sha256(raw.encode()).hexdigest()  # (valor p/ cliente, hash p/ DB)

# no refresh: localizar pelo hash; se já 'rotated_at' preenchido → reuso →
#   revogar todos os refresh da família (mesmo user/device) e exigir novo login.
# comparar com secrets.compare_digest quando aplicável.
```

### Pattern 5: RBAC por dependencies FastAPI compostas
**What:** Cadeia de dependencies: autenticar → resolver papel no contexto de área → exigir papel/escopo.
**When to use:** Toda rota de domínio.
**Example:**
```python
# Source: owasp-security SKILL.md §A01 (rotas admin: dependency separada) [CITED]
def require_role(*allowed: str):
    async def _dep(user: User = Depends(get_current_user),
                   scope: int | None = Depends(area_scope)) -> User:
        role = resolve_role(user, area_id=scope)   # area_admins / vínculos
        if role not in allowed:
            raise AppError("forbidden", code="forbidden")  # 403
        return user
    return _dep

require_platform_admin = require_role("admin_plataforma")  # dependency separada,
#                                       nunca `if user.is_admin` no corpo
```

### Anti-Patterns to Avoid
- **Filtro de área em `if` após o fetch:** esquecível, não compõe com paginação. Use `WHERE area_id` (Pattern 1). [owasp A01]
- **`jwt.decode` sem `algorithms=[...]` pinado:** habilita `alg:none`. [owasp A02]
- **`==` para comparar token/HMAC/código:** timing attack. Use `secrets.compare_digest`. [owasp A02/A08]
- **Mensagem de login revelando "usuário não existe":** enumeração de conta. Use "credenciais inválidas" único. [owasp A05/A07, RN-011]
- **`datetime.utcnow()` / `.replace(tzinfo=None)` em `exp`/lockout:** naive datetime — TD-010. Use `datetime.now(UTC)`.
- **`if user.is_admin` no corpo da rota:** use dependency separada `require_platform_admin`. [owasp A01]
- **Confiar só em convenção de app para imutabilidade do audit_log:** sem trigger não há garantia. [RN-012]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hash de senha | KDF próprio / sha256+salt | `argon2-cffi` `PasswordHasher` | sha-família é rápida demais por design; argon2id é memory-hard e venceu o PHC [owasp A02] |
| JWT encode/decode | parser de JWT manual | `PyJWT` com algoritmo pinado | parser manual erra validação de `exp`/`alg` e habilita `alg:none` [owasp A02] |
| TOTP | gerar HMAC-SHA1 + truncamento RFC 4226 à mão | `pyotp` | edge cases de janela/skew e provisioning URI; replay window correto |
| Comparação de segredo | `a == b` | `secrets.compare_digest` | timing-safe [owasp A02/A08] |
| Imutabilidade de log | só "não fazer UPDATE no código" | trigger MySQL `BEFORE UPDATE/DELETE` + `SIGNAL` | garantia no banco, não na disciplina [RN-012] |
| Redação de PII em log | lembrar em cada `logger.info` | filtro central de logging (Phase 1 já tem) | "confiar que cada log vai lembrar é design para falhar" [owasp A09] |

**Key insight:** auth e isolamento multi-tenant são exatamente o tipo de domínio onde "quase certo" é uma vulnerabilidade. Toda a frente desta phase deve apoiar-se em bibliotecas maduras e garantias estruturais (query + trigger + dependency), nunca em disciplina de código.

## Multi-área isolation patterns (MySQL 8 sem RLS nativo)

MySQL 8 **não possui Row-Level Security nativo** (diferente de PostgreSQL `CREATE POLICY`). [VERIFIED: ausência confirmada — MySQL não oferto `ROW LEVEL SECURITY`; padrão de mercado para multi-tenant MySQL é escopo na camada de aplicação]. Logo, o isolamento de área é implementado em **3 camadas defensivas**:

1. **Schema (DB):** mixin `AreaScopedMixin` → `area_id BIGINT NOT NULL` + índice `ix_<table>_area_id` + FK para `areas` (RESTRICT — DRV-002). Toda tabela de domínio herda. Tabelas globais (`users`, `audit_log`, `ai_usage_log`) NÃO herdam (D-05).
2. **Aplicação (query):** `AreaScopedRepository` base cujos métodos (`get_for_area`, `list_for_area`) sempre injetam `WHERE area_id = :scope`. Repositórios de domínio herdam dele; é o ponto único onde o filtro vive (Pattern 1). Não há método de leitura de domínio sem `area_id`.
3. **Autorização (dependency):** `area_scope` resolve o escopo a partir do token (`area_scope` claim) e do path (`/v1/areas/{area_id}/...`); se o `area_id` do path ≠ escopo do token e o papel não é `admin_plataforma` → **403** (D-06, F-08 E1). Admin de plataforma pode passar `area_scope=None` e operar cross-área, **mas todo acesso cross-área dele grava em `audit_log`** com a flag de bypass (RN-001, não silencioso).

**Resolução de papel por contexto de área (D-09):** um `user` pode ser owner de loja na área 1 e entregador na área 2. `resolve_role(user, area_id)` consulta os vínculos (nesta phase só `area_admins`; merchant_users/couriers chegam nas phases futuras) e retorna o papel **naquela** área. O JWT carrega o papel/escopo do contexto da sessão atual; trocar de contexto re-emite ou re-resolve.

**Teste de isolamento (critério de aceite — D-07):** seed de 2 áreas com 1 `area_admin` cada; admin da área A faz `GET /v1/areas/{B}/...` → espera 403; admin plataforma faz o mesmo → 200 **e** uma linha em `audit_log` com o bypass. Listagem de domínio scoped à área A nunca retorna linha da área B (vazio/filtrado).

## Append-only via trigger MySQL (RN-012)

`audit_log` (e futuras tabelas de transição) são INSERT-only **garantido pelo banco**. A migration Alembic cria a tabela e, via `op.execute()`, os triggers:

```sql
-- Source: padrão MySQL SIGNAL para abortar DML (RN-012) [CITED: MySQL 8 SIGNAL docs]
CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON audit_log
FOR EACH ROW SIGNAL SQLSTATE '45000'
  SET MESSAGE_TEXT = 'audit_log is append-only (RN-012)';

CREATE TRIGGER trg_audit_log_no_delete BEFORE DELETE ON audit_log
FOR EACH ROW SIGNAL SQLSTATE '45000'
  SET MESSAGE_TEXT = 'audit_log is append-only (RN-012)';
```

**Atenção (downgrade):** a migration `downgrade()` deve `DROP TRIGGER IF EXISTS` antes de dropar a tabela. **Atenção (dev SQLite):** specs/stack.yaml prevê SQLite via aiosqlite em dev — a sintaxe de trigger difere (SQLite usa `BEFORE UPDATE ... BEGIN SELECT RAISE(ABORT,...); END`). Ver LOW-3: decidir se o teste de trigger roda só contra MySQL (recomendado: o teste de append-only é critério de aceite contra **MySQL 8**, ambiente de CI sobe MySQL).

## Common Pitfalls

### Pitfall 1: Naive datetime em `exp` e janelas de lockout (TD-010)
**What goes wrong:** `datetime.utcnow()` retorna naive; comparar com `datetime.now(UTC)` (aware) lança `TypeError`, ou pior, compara errado silenciosamente após `.replace(tzinfo=None)`.
**Why it happens:** hábito antigo; PyJWT aceita tanto aware quanto naive para `exp` (interpreta naive como UTC), o que mascara o bug até a comparação de lockout.
**How to avoid:** SEMPRE `datetime.now(UTC)`. O projeto já tem ruff `DTZ` (flake8-datetimez) ligado e um AST guard custom — confiar neles, mas revisar o módulo `security.py` manualmente.
**Warning signs:** ruff `DTZ` warning; `TypeError: can't compare offset-naive and offset-aware datetimes` em teste de lockout.

### Pitfall 2: Enumeração de conta por timing ou mensagem (RN-011)
**What goes wrong:** se o e-mail não existe, pular o `argon2.verify` retorna mais rápido → atacante distingue contas por latência; ou mensagem "usuário não encontrado".
**Why it happens:** otimização ingênua ("não tem user, retorna logo").
**How to avoid:** rodar `argon2.verify` contra um hash dummy mesmo quando o user não existe (tempo constante); mensagem única "Credenciais inválidas". Na colisão de cadastro (REQ-006): "Já existe conta com esse dado. Recuperar acesso?" sem dizer QUAL dado. [owasp A05/A07]
**Warning signs:** tempos de resposta de login muito diferentes para e-mail existente vs. inexistente.

### Pitfall 3: TOTP replay e clock skew
**What goes wrong:** mesmo código TOTP aceito duas vezes (replay) ou recusado por skew de relógio.
**Why it happens:** não invalidar o último código usado; `valid_window` mal calibrado.
**How to avoid:** `TOTP.verify(code, valid_window=1)` (±30s de tolerância) e **persistir o último `counter`/código aceito** para recusar replay dentro da mesma janela. [owasp A07]
**Warning signs:** mesmo 6-dígitos funciona duas vezes seguidas em teste.

### Pitfall 4: Refresh sem rotação vira sessão eterna
**What goes wrong:** refresh reaproveitável indefinidamente; roubo do refresh = acesso permanente.
**Why it happens:** persistir refresh sem rotacionar nem detectar reuso.
**How to avoid:** rotação a cada uso + detecção de reuso (token já rotacionado usado de novo = comprometido → revogar família). Refresh com hash em DB, valor opaco no cliente. [owasp A02]
**Warning signs:** mesmo refresh aceito após já ter gerado um novo par.

### Pitfall 5: `area_id` esquecido em uma query nova
**What goes wrong:** um endpoint futuro consulta tabela de domínio sem filtrar área → vazamento cross-área.
**Why it happens:** filtro deixado a cargo de cada autor de query.
**How to avoid:** `AreaScopedRepository` é o único caminho de acesso a tabelas de domínio; review/lint que bloqueie `select(DomainModel)` fora do repositório base. Teste de isolamento por módulo (D-07).
**Warning signs:** `select(` de modelo de domínio fora de `repository.py`.

## Code Examples

### Lockout 5/15min com datetime aware (RN-011 / D-04)
```python
# Source: owasp-security SKILL.md §A07 (lockout progressivo) [CITED]
from datetime import datetime, timedelta, UTC

LOCK_THRESHOLD, LOCK_WINDOW = 5, timedelta(minutes=15)

def register_failed_attempt(user) -> None:
    now = datetime.now(UTC)  # AWARE — TD-010
    if user.first_failed_at is None or now - user.first_failed_at > LOCK_WINDOW:
        user.first_failed_at, user.failed_attempts = now, 1
    else:
        user.failed_attempts += 1
    if user.failed_attempts >= LOCK_THRESHOLD:
        user.locked_until = now + LOCK_WINDOW   # responde 423/429 até passar

def is_locked(user) -> bool:
    return user.locked_until is not None and datetime.now(UTC) < user.locked_until
```

### Write de audit_log com before/after (D-11) + bypass auditado (RN-001)
```python
# Source: entidades.md (audit_log before/after) + RN-001 (bypass não silencioso)
async def write_audit(session, *, actor_id, action, area_id, before, after, ip,
                      cross_area_bypass=False):
    session.add(AuditLog(
        actor_user_id=actor_id, action=action, area_id=area_id,
        before=before, after=after, ip=ip,
        cross_area_bypass=cross_area_bypass,     # True quando admin plataforma sai do escopo
        created_at=datetime.now(UTC),            # AWARE — TD-010
    ))
    # NUNCA logar PII no structlog; audit_log é tabela, não log de aplicação.
```

## Security Baseline

> **Gate 4 (obrigatório).** Fonte: `.claude/skills/owasp-security/SKILL.md` (OWASP Top 10:2025 / ASVS 5.0). Threat model curto (owasp A04): *quem pode abusar? o que ganha? qual o pior caso?* O `threat_model` do PLAN.md herda desta seção.

### Applicable ASVS / OWASP Categories

| OWASP/ASVS | Aplica | Controle padrão nesta phase |
|------------|--------|------------------------------|
| A01 Broken Access Control | sim | RBAC por dependency; `WHERE area_id` na query; 404 cross-área; rota admin com dependency separada |
| A02 Cryptographic Failures | sim | argon2id; HS256 com algoritmo pinado e claims obrigatórias; refresh opaco hasheado; `compare_digest` |
| A03 Injection | sim | SQLAlchemy parametrizado; Pydantic v2 `extra="forbid"` em escrita; allowlist em ORDER BY |
| A04 Insecure Design | sim | lockout derivado (5/15min por conta); invariantes de auth no servidor; threat model abaixo |
| A05 Security Misconfiguration | sim | mensagem de login genérica; `/docs` atrás de auth/desligada em prod; sem stack trace no corpo |
| A07 Identification & Auth Failures | sim | senha mín. 10–12 chars sem composição arbitrária (NIST 800-63B); lockout; TOTP admin; invalidar sessão na troca de senha |
| A08 Integrity Failures | sim | `compare_digest` em comparações; sem `pickle`/`eval` |
| A09 Logging Failures | sim | logar login sucesso/falha, mudança de permissão, acesso admin; **PII nunca em log** (filtro central Phase 1) |
| V6 Cryptography (ASVS) | sim | nunca hand-roll; argon2-cffi / PyJWT / pyotp / stdlib `secrets` |

### Threat model (ameaça → mitigação concreta citando owasp-security)

| # | Ameaça (STRIDE) | Mitigação concreta | Fonte owasp-security |
|---|------------------|--------------------|----------------------|
| 1 | **Força bruta / credential stuffing** no login (Spoofing) | Lockout 5 tentativas/15 min **por conta** (423/429); argon2id (memory-hard, caro de atacar offline); avaliar 2ª dimensão por IP (Redis) se necessário | A04 (rate limit login: "5/min por IP **e** por conta"), A07 (lockout progressivo), A02 (argon2id) |
| 2 | **Roubo de token** (access ou refresh) (Spoofing/Tampering) | Access HS256 curto (15 min); refresh **opaco** (não-JWT), hash SHA-256 em DB, **rotação a cada uso + detecção de reuso** (revoga família); refresh em cookie **httpOnly+Secure** (web) / Secure Storage (app); `algorithms=["HS256"]` pinado no decode (anti `alg:none`) | A02 ("refresh opacos, hash no banco, rotacionados, detecção de reuso"; "algoritmo pinado no decode") |
| 3 | **Reuso de refresh comprometido** (Spoofing) | Refresh já rotacionado usado de novo = sessão comprometida → revogar a **família inteira** + exigir novo login | A02 ("reuso de refresh já rotacionado = sessão comprometida → revogar a família inteira") |
| 4 | **Enumeração de conta** no login e no cadastro (Information Disclosure, RN-011) | Mensagem única "Credenciais inválidas"; rodar `argon2.verify` contra hash dummy mesmo sem user (tempo constante); colisão de cadastro → "Já existe conta com esse dado. Recuperar acesso?" sem revelar QUAL dado | A05 ("'credenciais inválidas' — nunca 'usuário não existe'"), A07 |
| 5 | **Escalonamento de privilégio cross-área** (Elevation of Privilege, RN-001) | `area_scope` na **query** (`WHERE area_id`), não em `if`; admin de área acessando outra área → **403** (F-08 E1); recurso de outra área → **404** (não vaza existência); `require_role` como dependency, não `if` no corpo | A01 ("tenant_id no WHERE de todo repositório, não em if"; "404 (não 403) para recurso de outro tenant"; "rotas admin: dependency separada") |
| 6 | **Bypass de admin de plataforma silencioso** (Repudiation) | Bypass de escopo do admin plataforma SEMPRE grava em `audit_log` com flag `cross_area_bypass`, ator, timestamp, IP — nunca silencioso (RN-001) | A09 ("logar mudança de permissão, acesso admin"), A01 (rotas admin auditadas) |
| 7 | **SQL injection** (Tampering) | Toda query via SQLAlchemy parametrizado; nenhum f-string em SQL (FAIL-BLOCK); Pydantic v2 com tipos estreitos + `extra="forbid"` (anti mass-assignment); allowlist em `ORDER BY` | A03 ("SQL apenas via ORM/prepared; f-string = FAIL-BLOCK"; "Pydantic v2, extra='forbid'") |
| 8 | **TOTP replay** (Spoofing) | `TOTP.verify(code, valid_window=1)`; persistir último código/janela aceito e recusar repetição dentro da janela; segredo TOTP nunca exposto em API/tela | A07 (MFA), A02 (segredos), RN-007 (código nunca exposto) |
| 9 | **PII em log de aplicação** (Information Disclosure, RN-021) | NUNCA logar senha (nem errada), token/refresh, CPF/CNPJ completo, corpo de request de auth; redação **estrutural** via filtro central já existente (config: `pii_fields_forbidden_in_logs`); CPF mascarado em respostas que não exigem o dado | A09 ("PII em log = FAIL-BLOCK"; "redação estrutural, não disciplina"), LGPD |
| 10 | **Tampering do audit_log** (Tampering/Repudiation, RN-012) | Trigger MySQL `BEFORE UPDATE/DELETE` com `SIGNAL SQLSTATE '45000'` aborta qualquer DML destrutiva; garantia no banco, não em convenção; teste automatizado (UPDATE → erro MySQL) é critério de aceite | A08 (integridade de dados), RN-012 |

### Decisões de segurança a registrar no PLAN.md (derivação obrigatória)
- **Lockout 5/15min:** derivado de ADR-005 + A04 (login deve inviabilizar brute force sem punir caps lock). Documentar a derivação (owasp A04 exige número derivado, não copiado).
- **Política de senha:** mínimo 10–12 chars, sem regras de composição arbitrárias (NIST 800-63B / A07). Confirmar mínimo no PLAN.
- **Segredo JWT (`JWT_SECRET`):** ≥256 bits, só via env (nunca no repo); rotação = invalida tokens vivos (aceitável p/ access 15min). Adicionar a `core/config.py` (hoje não existe campo de auth lá). [owasp Gestão de Segredos]

## Runtime State Inventory

> Greenfield desta phase (cria tabelas novas, não renomeia nada). Não obstante, há um item de config a registrar:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Nenhuma tabela pré-existente desta phase — `users/areas/area_admins/audit_log/refresh_tokens` são novas migrations | criar migrations Alembic |
| Live service config | Nenhuma — None (verificado: Phase 1 só tem health/observabilidade) | nenhuma |
| OS-registered state | Nenhuma — None | nenhuma |
| Secrets/env vars | **Novo segredo `JWT_SECRET`** (≥256 bits) a adicionar em `core/config.py` + `.env`/`.env.example` (placeholder); não existe hoje | adicionar campo em Settings; injetar via env em prod |
| Build artifacts | Nenhum — `uv add` atualiza `uv.lock`; sem egg-info | commitar `uv.lock` |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| MySQL 8 | trigger append-only + FK + índices | ✓ (Docker Compose Phase 1) | 8.x | SQLite em dev (sintaxe de trigger difere — ver LOW-3) |
| `argon2-cffi` | hash de senha | a instalar (`uv add`) | 25.1.0 | — (sem fallback aceitável; bcrypt proibido) |
| `PyJWT` | access token | a instalar | 2.13.0 | python-jose (não recomendado) |
| `pyotp` | TOTP | a instalar | 2.9.0 | — |
| Redis 7 | (opcional) lockout por IP | ✓ (Phase 1) | 7.x | coluna no DB (suficiente no M1) |

**Missing dependencies with no fallback:** nenhuma bloqueante — as 3 libs são instaláveis via `uv add` do registro público (versões verificadas em 2026-06-10).

## Validation Architecture

> config.json não define `workflow.nyquist_validation` → tratado como habilitado. Infra de teste vem da Phase 1 (pytest + pytest-asyncio).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio (asyncio_mode=auto) |
| Config file | `apps/api/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd apps/api && uv run pytest -q` |
| Full suite command | `cd apps/api && uv run pytest && uv run ruff check .` |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | File |
|-----|----------|-----------|-------------------|------|
| REQ-001 | cross-área admin de área → 403; listagem scoped vazia p/ outra área | integration | `uv run pytest tests/test_area_isolation.py -x` | ❌ Wave 0 |
| REQ-001 | bypass admin plataforma → 200 + linha em audit_log | integration | `uv run pytest tests/test_area_isolation.py::test_platform_bypass_audited` | ❌ Wave 0 |
| REQ-004 | UPDATE em audit_log → erro MySQL | integration (MySQL) | `uv run pytest tests/test_audit_append_only.py -x` | ❌ Wave 0 |
| REQ-005 | 6ª tentativa em 15 min → 423/429 | unit/integration | `uv run pytest tests/test_auth_lockout.py -x` | ❌ Wave 0 |
| REQ-005 | login feliz → access(15min)+refresh; refresh rotaciona; reuso revoga família | integration | `uv run pytest tests/test_auth_flow.py -x` | ❌ Wave 0 |
| REQ-005 | admin plataforma sem TOTP → forçado a configurar | integration | `uv run pytest tests/test_totp.py -x` | ❌ Wave 0 |
| REQ-006 | colisão de cadastro → mensagem genérica (não revela qual dado) | unit | `uv run pytest tests/test_anti_enumeration.py -x` | ❌ Wave 0 |
| REQ-007 | matriz de permissões por papel (operador→403 em financeiro etc.) | integration | `uv run pytest tests/test_rbac_matrix.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest -q` (subset do módulo tocado)
- **Per wave merge:** `uv run pytest && uv run ruff check .`
- **Phase gate:** suíte completa verde + os 3 testes de aceite do ROADMAP (isolamento, trigger, lockout) verdes antes de `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — fixtures: app, sessão async, seed de 2 áreas + 2 area_admins, factory de user
- [ ] `tests/test_area_isolation.py` — REQ-001 (403 cross-área + bypass auditado)
- [ ] `tests/test_audit_append_only.py` — REQ-004 (trigger; **roda contra MySQL no CI**)
- [ ] `tests/test_auth_lockout.py`, `test_auth_flow.py`, `test_totp.py` — REQ-005
- [ ] `tests/test_anti_enumeration.py` — REQ-006
- [ ] `tests/test_rbac_matrix.py` — REQ-007
- [ ] CI: garantir job de teste sobe **MySQL 8** (não só SQLite) para o teste de trigger

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| bcrypt para senha | argon2id (memory-hard) | OWASP recomenda argon2id como 1ª opção | ADR-005 já trava argon2id |
| `datetime.utcnow()` (naive) | `datetime.now(UTC)` (aware) | deprecado em Python 3.12+ | ruff DTZ + AST guard ativos (TD-010) |
| JWT como refresh token | refresh **opaco** rotacionável em DB | prática atual (revogabilidade) | ADR-005 já trava refresh opaco |
| python-jose | PyJWT | manutenção/CVEs de jose | recomendação desta pesquisa |

**Deprecated/outdated:**
- `datetime.utcnow()` / `datetime.utcfromtimestamp()`: deprecados — usar aware UTC.
- MFA por SMS: rejeitada por ADR-005 (TOTP only).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `PasswordHasher` defaults da argon2-cffi 25.1.0 estão ≈ recomendação OWASP atual | Standard Stack / Pattern 2 | Parâmetros sub/super-dimensionados; mitigado setando parâmetros explícitos (LOW-1) |
| A2 | CI sobe MySQL 8 para o teste de trigger (não só SQLite) | Validation Architecture | Teste de append-only não roda de verdade em SQLite com mesma sintaxe (LOW-3) |
| A3 | Lockout por conta (coluna no DB) é suficiente no M1, sem necessidade de 2ª dimensão por IP | Security Baseline ameaça 1 | Brute force distribuído por IPs diferentes não é coberto; aceitável no piloto, revisitar |

## Open Questions / LOW-confidence (Regra 12 — cada um vira task no PLAN ou TD com urgency_class)

1. **LOW-1 — Parâmetros exatos de argon2id.** [confidence: LOW]
   - O que sabemos: `PasswordHasher()` traz defaults razoáveis; OWASP sugere algo como `time_cost=2, memory_cost=19 MiB, parallelism=1` (m=19456 KiB) como ponto de partida, calibrado por tempo-alvo (~50–100ms no hardware de prod).
   - O que falta: confirmar o alvo OWASP vigente e calibrar `memory_cost` ao hardware do VPS de produção.
   - Recomendação: **vira TASK no PLAN** — "definir e fixar parâmetros argon2id explícitos + benchmark de ~100ms no hardware-alvo; usar `check_needs_rehash` para upgrade futuro". Critério de aceite verificável (parâmetros pinados no código + teste de tempo). specs/stack.yaml diz "custo 12" (terminologia de bcrypt) — **não aplicar literalmente a argon2**; tratar como "parâmetros recomendados OWASP".

2. **LOW-2 — Escolha final de lib JWT (PyJWT vs python-jose).** [confidence: MEDIUM-LOW]
   - O que sabemos: PyJWT é recomendada (mais simples, segura por default para HS256).
   - O que falta: confirmar que nenhuma necessidade futura (JWE/assimétrico para Menu Certo) exige jose desde já.
   - Recomendação: **vira TASK no PLAN** — "fixar PyJWT; documentar em nota que migração a RS256 (multi-validador) seria ADR". Baixo risco; decisão registrada evita re-litígio.

3. **LOW-3 — Sintaxe de trigger append-only em dev (SQLite) vs CI/prod (MySQL).** [confidence: MEDIUM]
   - O que sabemos: a garantia real é MySQL; SQLite usa `RAISE(ABORT)`.
   - O que falta: decidir se a migration emite trigger condicional por dialeto ou se o teste de aceite roda só contra MySQL.
   - Recomendação: **vira TASK no PLAN** — "teste de append-only roda contra MySQL 8 no CI; migration usa `op.execute` MySQL-específico com guarda de dialeto". Se não resolvido, **vira TD** `urgency_class: pre_launch_high` (critério de aceite do ROADMAP depende disso).

## Project Constraints (from CLAUDE.md / specs)
- **DRV-002:** soft delete (`deleted_at`) em domínio; FK RESTRICT; utf8mb4; UTC no banco. → `areas`/`area_admins` com `deleted_at`; `users` global também soft-delete (anonimização LGPD).
- **DRV-003:** `/v1/`, erros RFC 7807, idempotência por header em escrita relevante. → endpoints sob `/v1/auth/*`, `/v1/areas/*`; reaproveitar error envelope da Phase 1.
- **SQL puro não aceito (specs):** trigger entra via `op.execute()` dentro de migration Alembic, não como `.sql` solto.
- **PII proibida em log (config.json):** `cpf, cnpj, email, password, token, jwt, ...` já na denylist do filtro central — não burlar.
- **Naive datetime guard (TD-010 + ruff DTZ):** todo datetime aware UTC.

## Sources

### Primary (HIGH confidence)
- `.claude/skills/owasp-security/SKILL.md` — A01, A02, A03, A04, A05, A07, A08, A09, Gestão de Segredos (fonte do Security Baseline)
- `.planning/DECISIONS.md` — ADR-001 (multi-área), ADR-005 (auth), DRV-002/003
- `projeto/regras-negocio/regras.md` — RN-001, RN-011, RN-012, RN-021, RN-022
- `projeto/regras-negocio/entidades.md` — §Núcleo multi-área, audit_log, invariantes
- `.planning/REQUIREMENTS.md` — REQ-001/002/004/005/006/007
- `apps/api/app/*` — código Phase 1 (factory, sessão async, middleware com user_id reservado, error envelope, base utf8mb4/UTC)
- Context7 `/hynek/argon2-cffi` — PasswordHasher, check_needs_rehash, parameters
- PyPI (`pip index versions`, 2026-06-10) — argon2-cffi 25.1.0, PyJWT 2.13.0, pyotp 2.9.0

### Secondary (MEDIUM confidence)
- `.claude/skills/br/lgpd-compliance/SKILL.md` — minimização, base legal, mascaramento PII
- specs/stack.yaml — auth: argon2id, JWT short-lived + refresh rotation, httpOnly cookie admin / Secure Storage mobile

### Tertiary (LOW confidence — marcado p/ validação)
- Parâmetros exatos argon2id (LOW-1) — confirmar alvo OWASP vigente no PLAN
- Sintaxe trigger SQLite vs MySQL (LOW-3)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no PyPI; libs canônicas
- Architecture (multi-área, RBAC, append-only): HIGH — padrões diretos de owasp-security + ADRs travados
- Security Baseline: HIGH — cada ameaça mapeada a seção concreta de owasp-security
- Parâmetros argon2id: LOW — defaults vs alvo OWASP (LOW-1)
- Trigger em dev SQLite: MEDIUM — garantia real é MySQL (LOW-3)

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (30 dias — stack estável; reverificar versões antes de execução se atrasar)
