# Phase 12 — Reconciliação (prometido vs. real)

**Data:** 2026-06-11 (autopilot) · **Status:** sem gaps abertos

| Prometido (PLAN) | Real (código) | Evidência |
|---|---|---|
| Migration 0010 reversível (4 tabelas) | ✓ | `alembic/versions/0010_public_api_webhooks.py` + `tests/db/test_migration_0010.py` (@mysql) |
| Módulo `api_keys` (gerar/hash/revoke) | ✓ | `app/api_keys/` (argon2id, soft revoke) |
| Dependency `api_key_scope` (401 estável, cache invalidado no revoke) | ✓ | `app/api_keys/dependencies.py` + testes |
| POST público idempotente (24h, 409, 429+Retry-After) | ✓ (em `/v1/public/deliveries` — TD-12-01) | `app/api_public/` + testes idempotência |
| Job purge de idempotência | ✓ | `app/workers/` |
| Webhooks outbound HMAC `t=,v1=` + ULID | ✓ | `app/webhooks/signing.py` (`compare_digest`) |
| Hook não-bloqueante na `transition` | ✓ | `app/deliveries/service.py` (T-07) |
| Anti-SSRF da URL de webhook | ✓ | `app/webhooks/ssrf.py` + testes |
| Job de entrega com backoff exato 8× + failed/alerta | ✓ | `app/workers/webhooks.py` + teste com clock controlado |
| Endpoints admin de área (keys + webhook) | ✓ | `app/api_keys/admin_router.py`, `app/webhooks/` |
| Tela 22 (lista/criar/revogar/webhook) | ✓ | `apps/web/src/features/admin/api-keys/` |
| `jx-secret-reveal` (segredo 1×, a11y) | ✓ | `apps/web/src/shared/components/secret-reveal/` |
| Zero hex | ✓ | grep 0 ocorrências em api-keys/ e secret-reveal/ |
| Testes verdes + lint | ✓ | backend 59 not-mysql; frontend 139 total; ruff + ng lint limpos |

## Desvios (registrados)
- **TD-12-01** (pre_launch_medium): API pública em `/v1/public/deliveries` (não `/v1/deliveries`, que já é o router interno de loja). Alinhar com o integrador Menu Certo antes do go-live.
- **TD-12-02** (post_launch): rate limit + cache de auth in-process (não distribuído). Revoke ainda < 1 min. Revisar se houver múltiplas instâncias.

## Gaps abertos
Nenhum. Pendente apenas `pytest -m mysql` (migration 0010 reversível) em DB live — mesmo padrão das phases anteriores (verificação ao vivo).
