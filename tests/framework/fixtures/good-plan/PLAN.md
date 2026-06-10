# PLAN.md — Phase 2 (good-plan fixture)

## Objetivo
Adicionar endpoint POST /api/v1/orders com validação de CPF.

## Skills Consultadas

- `product/api-design-contracts` — response shape, error codes, idempotency
- `br/brazilian-forms` — validação de CPF no backend
- `quality/observability-production` — logs estruturados sem PII
- `quality/error-ux-patterns` — error codes tipados

## Skills Dispensadas

Nenhuma — esta fase não mexe em UI, mobile nativo, push, i18n de locales novos.

## Tasks

- [ ] T1: Criar schema `CreateOrderBody` (Pydantic)
- [ ] T2: Endpoint POST /api/v1/orders com `response_model=OrderResponse`
- [ ] T3: Validação CPF usando helper `validate_cpf()`
- [ ] T4: Error codes `VALIDATION_CPF_INVALID`, `RESOURCE_ALREADY_EXISTS`
- [ ] T5: Idempotency-Key header obrigatório
- [ ] T6: Logs com request_id, sem CPF em cleartext
- [ ] T7: Testes: 201 sucesso, 422 CPF inválido, 409 duplicate, snapshot OpenAPI

## Critérios de aceite

- Endpoint retorna 201 com `{data: {...}}` em sucesso
- Validação CPF rejeita entrada inválida com code `VALIDATION_CPF_INVALID`
- Idempotency-Key dedupe funciona (mesma key = mesma response 200)
- Zero CPF em logs (grep em /var/log confirma)
- OpenAPI schema atualizado

## Gates aplicáveis

Gate 3 (skills), Gate 4 (observability), Gate 6 (tests), Gate 7 (docs).
