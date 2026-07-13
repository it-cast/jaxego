# CORRECAO-235 — Fix: `Courier` sem `user_id` quebrava upload de documentos

## Data
2026-07-13

## Sintoma
Ao cadastrar o entregador e enviar as fotos dos documentos, a API retornava 500:
```
AttributeError: 'Courier' object has no attribute 'user_id'
File "app/couriers/service.py", line 129, in presign_document
```

## Causa raiz
Sobra da CORRECAO-230 (remoção da tabela `users`): `couriers.user_id` foi
removido do model, mas três `write_audit(actor_id=courier.user_id, ...)`
sobreviveram à refatoração porque não apareceram nos greps anteriores (o
padrão buscado era `Courier.user_id` maiúsculo, não `courier.user_id` de
instância).

## Fix
- `app/couriers/service.py`:
  - `presign_document`: `actor_id=courier.user_id` → `actor_id=courier.id,
    actor_type="courier"`
  - `validate_mei`: idem
- `app/areas/router.py` `assign_area_admin`: `membership.user_id` (não existe
  mais em `AreaAdmin`) → `membership.id`; `AreaAdminRead` também estava sem
  `user_name`.

## Validado
Smoke test E2E com courier de teste (deletado ao final):
1. `POST /v1/couriers/signup` → 201
2. `POST /v1/couriers/{id}/documents` (presign) → 201 (antes: 500)
3. `POST /v1/couriers/{id}/documents/{doc_id}/complete` → 200, status `pending`
4. `audit_log` confirmado com `actor_type=courier` correto

## Lição
Ao remover uma coluna de um model (`user_id` em `Courier`/`AreaAdmin`/...),
grep por `\.user_id\b` (instância minúscula) pega mais casos do que grep só
pela classe (`Courier.user_id`, que só bate em queries `select()`/`where()`).
