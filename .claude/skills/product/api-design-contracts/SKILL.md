# API Design Contracts — response shape, error codes, versioning, OpenAPI

> Skill obrigatória para qualquer endpoint novo em API pública ou interna consumida por múltiplos clientes.

## Princípio central

A API é um **contrato**. Mudanças incompatíveis quebram clientes sem aviso. Um contrato bem desenhado é previsível (mesmo formato sucesso/erro em qualquer endpoint), versionado (clientes antigos funcionando), documentado automaticamente (OpenAPI gerado do código, não escrito à mão) e enforced (violações pegam no lint/type-check, não em produção).

## Response shape padronizado

### Sucesso (único item)

```json
{
  "data": {
    "id": "uuid",
    "name": "Exemplo",
    "created_at": "2026-04-22T10:00:00Z"
  }
}
```

### Sucesso (lista paginada — offset)

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

### Sucesso (lista paginada — cursor, para feeds grandes)

```json
{
  "items": [...],
  "next_cursor": "eyJpZCI6MTIzfQ==",
  "prev_cursor": null,
  "has_more": true
}
```

### Erro (sempre)

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Mensagem no locale do usuário",
    "field": "resource_id",
    "details": { "resource_id": "xxx" },
    "request_id": "7b8c9d..."
  }
}
```

- `code` — enum estável, cliente decide UX por ele
- `message` — legível, localizado via `Accept-Language`
- `field` — qual campo falhou (validação)
- `details` — contexto estruturado, não texto livre
- `request_id` — sempre, para correlação em logs

## Error codes enum centralizado

Nunca string mágica espalhada:

```python
# backend/app/core/errors.py
from enum import Enum

class ErrorCode(str, Enum):
    # Auth (AUTH_*)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    # Validation (VALIDATION_*)
    VALIDATION_CPF_INVALID = "VALIDATION_CPF_INVALID"
    VALIDATION_EMAIL_MALFORMED = "VALIDATION_EMAIL_MALFORMED"
    VALIDATION_FIELD_REQUIRED = "VALIDATION_FIELD_REQUIRED"
    # Resource (RESOURCE_*)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_DELETED = "RESOURCE_DELETED"
    # Business (BUSINESS_*)
    BUSINESS_QUOTA_EXCEEDED = "BUSINESS_QUOTA_EXCEEDED"
    BUSINESS_STATE_INVALID = "BUSINESS_STATE_INVALID"
    BUSINESS_DUPLICATE_ACTION = "BUSINESS_DUPLICATE_ACTION"
    # Rate limit / Infra
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
```

Cliente mobile/web mantém enum espelho. Teste de paridade:

```python
def test_mobile_client_has_all_codes():
    backend_codes = set(ErrorCode.__members__.keys())
    mobile_codes = set(json.load(open("mobile/src/error-codes.json")).keys())
    assert not (backend_codes - mobile_codes)
```

## HTTP semantics

| Status | Usar para | NÃO usar para |
|--------|-----------|---------------|
| 200 | GET sucesso; PUT/PATCH com body | POST create (use 201) |
| 201 | POST criou recurso | Update |
| 204 | DELETE, PUT/PATCH sem body | Qualquer coisa com body |
| 400 | Body malformado, JSON inválido | Negócio (use 409/422) |
| 401 | Sem credenciais ou inválidas | Sem permissão (403) |
| 403 | Autenticado sem permissão | Sem token (401) |
| 404 | Recurso não existe | Existe mas sem acesso (403) |
| 409 | Conflito (duplicate, race) | Validação campo (422) |
| 422 | Validação de negócio | Body malformado (400) |
| 429 | Rate limit | Quota negócio (use 403) |
| 5xx | Erro servidor | Erro cliente (4xx) |

**Anti-pattern crítico:** 200 com `{"success": false}` quebra middlewares, retry policies, logging. Sempre status code HTTP correto.

## Paginação

### Offset (admin, volumes pequeno-médio)
```
GET /api/v1/resources?page=2&page_size=20&sort=-created_at
```
- `page` 1-indexed; `page_size` default 20, max 100
- `sort` prefixo `-` = desc

### Cursor (feeds, volumes grandes)
```
GET /api/v1/feed?cursor=eyJ0cyI6MTcxNH0=&limit=50
```
- Cursor opaco (base64 de JSON com `id` + `sort_value`)
- Imutável ao inserir — preferido para timeline, feed, infinite scroll

### Nunca
- Paginação client-side (retornar 10k items para filtrar)
- Sem paginação
- Offset > 10000 (queries lentas, usar cursor)

## Versionamento

### URL path (recomendado)
```
/api/v1/resources
/api/v2/resources
```

### Política de deprecação
1. v2 lançada → documentada
2. v1 deprecated → header `Deprecation: true` + `Sunset: <date>` em todas responses
3. v1 removida → após 6-12 meses
4. Comunicação ativa ao deprecar

### Breaking vs non-breaking

**Non-breaking (pode em v1):**
- Novo endpoint, novo campo opcional na response, novo enum value (se cliente trata graciosamente), relaxar validação

**Breaking (exige v2):**
- Remover endpoint/campo, mudar tipo, apertar validação, mudar status code, renomear enum value

## Idempotency

POST/PATCH mutantes aceitam `Idempotency-Key`:

```
POST /api/v1/payments
Idempotency-Key: 8d7f9a2c-1b3e-4f5a-9c8d-7e6f5b4a3d2c
```

```python
@router.post("/payments")
async def create_payment(body, idempotency_key: str = Header(...), user=Depends(get_user)):
    cached = await redis.get(f"idem:{user.id}:{idempotency_key}")
    if cached:
        return json.loads(cached)
    result = await process_payment(body, user)
    await redis.setex(f"idem:{user.id}:{idempotency_key}", 86400, json.dumps(result))
    return result
```

GET/DELETE idempotentes por HTTP. PUT idempotente por convenção. POST/PATCH precisam header.

## Rate limiting por rota

```python
@router.post("/login")
@limiter.limit("5/minute", key_func=get_remote_address)
async def login(body): ...

@router.post("/password-reset")
@limiter.limit("3/hour")
async def password_reset(body): ...
```

Response 429 completa:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1713876000

{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "...", "retry_after_seconds": 60}}
```

Cliente consome `Retry-After` e mostra countdown.

## OpenAPI discipline (FastAPI)

### `response_model` obrigatório
```python
# ❌ sem schema
@router.get("/orders/{id}")
async def get_order(id: UUID):
    return await db.get_order(id)

# ✅ schema completo
@router.get("/orders/{id}", response_model=OrderResponse)
async def get_order(id: UUID) -> OrderResponse:
    return await db.get_order(id)
```

### `responses` para códigos 4xx/5xx
```python
@router.get(
    "/orders/{id}",
    response_model=OrderResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Order not found"},
        403: {"model": ErrorResponse, "description": "Not authorized"},
    },
)
```

### Schemas com `description` em campos críticos
```python
class CreateOrderBody(BaseModel):
    customer_id: UUID = Field(..., description="Cliente do workspace autenticado")
    amount: Decimal = Field(..., gt=0, max_digits=18, decimal_places=4, description="BRL, 0.01 a 999999999.99")
    payment_method: Literal["pix", "credit_card", "boleto"] = Field(..., description="Boleto compensa 1-3 dias úteis")
```

### Tags + exemplos
```python
@router.get("/orders", tags=["Orders"])

class OrderResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"id": "...", "status": "confirmed", "amount": "450.00"}]
    })
```

## Consistency across endpoints

**Timestamps:** ISO 8601 UTC com `Z`: `"2026-04-22T10:00:00Z"`. Nunca espaço, epoch ou `+00:00`.

**IDs:** string (não int — overflow em JS), UUID v4 ou v7.

**Booleans:** prefixo `is_`/`has_`/`can_`: `{"is_active": true, "has_verified_email": false}`.

**Money:** string decimal + currency:
```json
"amount": "450.00", "currency": "BRL"
```
ou objeto `{"value": "450.00", "currency": "BRL"}`. Nunca float/number.

**Enums:** strings snake_case, não ints mágicos: `"status": "confirmed"`.

**Null vs ausente:**
- `null` = campo existe sem valor (`"deleted_at": null`)
- Ausente = não aplicável ao recurso
- Ser consistente entre endpoints

## Filtering, sorting, search

```
GET /api/v1/orders?
  status=confirmed&
  status__in=confirmed,pending&
  amount__gte=100&
  created_at__gte=2026-01-01&
  search=cliente-xyz&
  sort=-created_at,name
```

Suffixes: `__eq`, `__ne`, `__gt`, `__gte`, `__lt`, `__lte`, `__in`, `__contains`, `__startswith`.

Whitelist de campos filtráveis — **nunca** aceitar qualquer campo:
```python
ALLOWED_FILTERS = {"status", "amount", "created_at", "customer_id"}
```

## Webhook contracts

Payload padrão:
```json
{
  "event_id": "evt_abc123",
  "event_type": "order.confirmed",
  "timestamp": "2026-04-22T10:00:00Z",
  "version": "v1",
  "data": {...}
}
```

Assinatura HMAC obrigatória:
```
POST /webhook
X-Signature: sha256=abcd1234...
X-Timestamp: 1713876000
```

Cliente valida: assinatura + timestamp dentro de 5 min (previne replay).

Retry: 2xx = ok; 5xx/timeout = exponential (1s, 5s, 30s, 5min, 30min, 2h). Após N: failed + notificação.

## Anti-patterns

- RPC-style (`POST /api/doStuff`) em vez de REST
- Versioning por query string (`?v=2`) — quebra CDN cache
- Campos com nomes diferentes (`userId` aqui, `user_id` ali)
- 500 para validação (use 400/422)
- 200 + `error: true` no body
- Query string com lógica (`?action=cancel` → `POST /orders/{id}/cancel`)
- Exposição direta de auto-increment IDs (facilita scraping, vaza contagem)
- `response_model=None` ou `Any`
- Docs em Confluence/Notion à parte do código

## Testing contracts

```python
def test_create_order_returns_201_with_id(client, auth):
    r = client.post("/api/v1/orders", json={"amount": "100"}, headers=auth)
    assert r.status_code == 201
    assert "id" in r.json()
    assert r.json()["created_at"].endswith("Z")

def test_invalid_amount_returns_422_with_code(client, auth):
    r = client.post("/api/v1/orders", json={"amount": "-10"}, headers=auth)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_AMOUNT_INVALID"
    assert r.json()["error"]["field"] == "amount"
```

Snapshot do OpenAPI previne breaking acidental:
```python
def test_openapi_schema_unchanged():
    schema = app.openapi()
    with open("tests/openapi.baseline.json") as f:
        baseline = json.load(f)
    assert schema == baseline, "OpenAPI mudou — revise breaking changes"
```

## Checklist para PLAN.md

- [ ] Todo endpoint tem `response_model` tipado
- [ ] 4xx/5xx documentados em `responses` com `ErrorResponse`
- [ ] Error codes novos no enum central
- [ ] Status codes corretos (201 create, 204 delete, 422 validação)
- [ ] Paginação definida (offset vs cursor)
- [ ] Versionamento considerado
- [ ] Rate limit por rota
- [ ] `Idempotency-Key` em POST/PATCH mutantes
- [ ] Timestamps ISO 8601 UTC
- [ ] Money string decimal + currency
- [ ] Snapshot OpenAPI atualizado
- [ ] Testes de contract (status, schema, error code)
