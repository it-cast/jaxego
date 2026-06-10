# Skill: fastapi-production-patterns

> Padrões de produção para backend FastAPI + Python 3.11/3.13 + SQLAlchemy 2.0 async + MySQL 8: estrutura de projeto, Pydantic v2, auth JWT, erros padronizados, rate limit, background jobs, testes.
> Categoria: `domain` · v0.9.5 · 2026-06-09

## Propósito

Fechar o gap mais grave do catálogo até v0.9.4: o framework tinha skill para Angular, Ionic, MySQL, Docker e LLM — mas **nenhuma para o backend FastAPI**, que é a camada onde nascem endpoints, auth, contratos e a maioria dos bugs de integração. Esta skill define o backend canônico que `api-design-contracts` (contrato) e `owasp-security` (ameaças) assumem existir.

## Quando usar (triggers)

- Qualquer phase com `has_api: true` ou que crie/altere endpoint
- Bootstrap de backend novo
- Auth, middleware, dependency injection
- Background jobs (Arq), integração Redis
- Code review de router/service/repository

---

## 1. Estrutura canônica de projeto

```
backend/
├── src/
│   └── app/
│       ├── main.py              # create_app() factory — NUNCA lógica aqui
│       ├── core/
│       │   ├── config.py        # Settings (pydantic-settings), única fonte de env
│       │   ├── security.py      # JWT encode/decode, hashing (bcrypt via passlib)
│       │   ├── deps.py          # Depends() compartilhados: get_db, get_current_user
│       │   └── exceptions.py    # Hierarquia AppError + handlers
│       ├── api/
│       │   └── v1/
│       │       ├── router.py    # include_router de todos os módulos
│       │       └── <recurso>.py # APIRouter por recurso (users.py, orders.py)
│       ├── models/              # SQLAlchemy 2.0 Mapped[] (ver mysql-schema-design)
│       ├── schemas/             # Pydantic v2 — separar Create/Update/Read/InDB
│       ├── services/            # Regra de negócio — routers NÃO contêm lógica
│       ├── repositories/        # Queries — services NÃO escrevem SQL/ORM direto
│       └── workers/             # Arq tasks (jobs assíncronos)
├── alembic/
├── tests/
│   ├── conftest.py              # fixtures: app, client, db transacional
│   ├── unit/                    # services com repos mockados
│   └── integration/             # endpoints reais contra DB de teste
└── pyproject.toml               # [tool.pytest.ini_options] pythonpath = ["src"]
```

**Regras inegociáveis:**

1. **Router magro.** Router valida input (Pydantic faz), chama service, devolve schema. Zero `if` de negócio no router.
2. **Service não conhece HTTP.** Services levantam `AppError` (domínio), nunca `HTTPException`. Handler global traduz.
3. **Repository não conhece negócio.** Só persiste e consulta.
4. **`pythonpath = ["src"]` no pyproject** — sem isso pytest coleta 0 testes (bug de campo: Rota Certa phase-02).

## 2. Pydantic v2 — schemas

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # v2 — NÃO orm_mode
    id: str
    email: EmailStr
    created_at: datetime
```

- **Nunca** expor model SQLAlchemy direto no response — sempre schema `Read`.
- `Update` schemas: todos os campos `Optional`, usar `model_dump(exclude_unset=True)` no service.
- Dinheiro: `Decimal`, nunca `float` (consistente com `DECIMAL(10,2)` da mysql-schema-design).
- Locale pt-BR: mensagens de validação custom via `field_validator` quando expostas ao usuário final.

## 3. Erros padronizados (contrato com o frontend)

Formato único de erro — o frontend (Angular interceptor) depende disso:

```json
{ "error": { "code": "RESOURCE_NOT_FOUND", "message": "Pedido não encontrado", "details": {}, "request_id": "..." } }
```

```python
class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

class NotFoundError(AppError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"

class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"

@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": {...}})
```

- **Nunca** vazar traceback/SQL em produção (`debug=False`, handler genérico para `Exception` com log + 500 limpo).
- `request_id` via middleware (uuid4 por request, propagado nos logs) — pré-requisito da skill `observability-production`.

## 4. Auth JWT — baseline

- Access token curto (15–30min) + refresh token (httpOnly cookie ou storage seguro do app — **nunca** localStorage em web, ver `owasp-security`).
- `get_current_user` como `Depends()` único; variação `get_current_admin` que valida role.
- Senhas: bcrypt (passlib), custo 12. Nunca log de senha, nem hash.
- Rate limit em `/auth/login` e `/auth/refresh`: slowapi ou contadores em Redis (5 tentativas/min/IP). Sem isso, gate 4 (Security Baseline) deve bloquear.

## 5. DB async — armadilhas reais

```python
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
```

- `pool_recycle=3600` — MySQL mata conexões idle (wait_timeout); sem recycle, primeiro request da manhã dá `MySQL server has gone away`.
- **Uma session por request** via `Depends(get_db)`, commit no fim, rollback em exceção — nunca session global.
- N+1: `selectinload()` explícito em toda lista com relacionamento. Code review checa: endpoint de lista + relacionamento sem eager load = bloqueio.
- Alembic `env.py` **deve** respeitar `TEST_DATABASE_URL` quando setado (bug de campo: Rota Certa phase-04).

## 6. Background jobs (Arq + Redis)

- Job que altera dados críticos: idempotente (chave natural ou dedup por job_id).
- Retry com backoff: `max_tries=5`, falha final vai para log estruturado + alerta.
- Pin de versões compatíveis no pyproject (`arq>=0.26` exige `redis>=7.4` — conflito silencioso de campo, Rota Certa phase-03).

## 7. Testes — mínimo por phase com endpoint

| Tipo | O quê | Onde |
|---|---|---|
| Integration | Happy path de cada endpoint novo (status + shape do response) | `tests/integration/` |
| Integration | 1 caso de erro por endpoint (404/409/422) validando formato `{"error": {...}}` | `tests/integration/` |
| Unit | Regra de negócio não-trivial do service | `tests/unit/` |

- Client: `httpx.AsyncClient` + `ASGITransport` — não subir servidor real.
- DB de teste: transação com rollback por teste, ou DB efêmero — nunca o DB de dev.

## 8. Checklist de code review (executor e reviewer usam)

- [ ] Router sem lógica de negócio
- [ ] Response usa schema `Read`, nunca model ORM
- [ ] Erros seguem formato canônico `{"error": {...}}`
- [ ] Endpoints de lista: paginação obrigatória (`limit` ≤ 100 + `offset`/cursor) — **lista sem paginação não passa**
- [ ] Eager loading em relacionamentos de lista
- [ ] Auth: endpoint novo declarou explicitamente público ou protegido (default: protegido)
- [ ] Migration acompanhando mudança de model, reversível (`downgrade` real)
- [ ] Testes de integração do happy path + 1 erro

## Anti-patterns proibidos

1. `HTTPException` dentro de service (acopla domínio a HTTP)
2. `float` para dinheiro
3. Query no router
4. Endpoint de lista sem paginação
5. `except Exception: pass`
6. Credenciais/URLs hardcoded fora de `Settings`
7. Session SQLAlchemy compartilhada entre requests

## Relação com outras skills

- `product/api-design-contracts` — define o contrato; esta skill define a implementação
- `domain/mysql-schema-design` — tipos e migrations
- `owasp-security` — threat model que o §4 implementa
- `quality/observability-production` — logs estruturados sobre o `request_id` do §3
- `domain/docker-production-ready` — empacotamento do app desta skill
