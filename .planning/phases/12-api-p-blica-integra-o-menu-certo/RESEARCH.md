# Phase 12: API pública + integração Menu Certo - Research

**Status:** Ready for planning
**Date:** 2026-06-11 (autopilot)

## Objetivo

Como expor `POST /v1/deliveries` idempotente (REQ-041) autenticado por API key por área
(REQ-042 / RN-020), e webhooks outbound HMAC com retry (REQ-043), reusando o máximo do código
das Phases 7–10.

## Achados técnicos

### 1. Reuso do `create_delivery` service (decisão central)
A API pública **não** reimplementa criação de entrega. `app/deliveries/service.create_delivery`
já encapsula máquina de estados, estimativa mediana, limite de plano e disparo do cascade. A phase
adiciona apenas uma **camada de auth+idempotência** na frente:
- novo router `app/api_public/router.py` (ou `app/deliveries/public_router.py`) que resolve a área
  via API key, mapeia `merchant_external_ref`→`merchant_id`, e chama o mesmo service.
- **Confidence: HIGH** — o service já aceita `area_id`, `merchant_id`, `actor_user_id`, `body`.

### 2. Idempotência persistente 24h (ADR-010)
O header `Idempotency-Key` já é lido no router interno, mas sem persistência. Para a API pública,
F-04 E1 exige resposta idêntica em replay dentro de 24h:
- Tabela `api_idempotency_keys` (`api_key_id`, `idempotency_key`, `request_hash` SHA-256 do body
  canônico, `response_status`, `response_body` JSON, `delivery_id`, `created_at`, `expires_at`).
- Fluxo: na entrada, `SELECT ... FOR UPDATE` por `(api_key_id, idempotency_key)`. Se existe e
  `request_hash` confere → retorna snapshot. Se existe com hash diferente → 409. Se não existe →
  cria a entrega, grava snapshot, retorna 201.
- Limpeza por job arq (purge `expires_at < now`), aware-UTC, idempotente (padrão das Phases 5/9).
- **Confidence: HIGH** — padrão clássico, infra arq já existe.

### 3. API keys com hash (RN-020)
- `app/api_keys/` módulo. Segredo gerado com `secrets.token_urlsafe(32)`, prefixado
  `jxg_<key_id8>_`. Persiste **apenas** argon2id hash (`app.core.security.hash_secret` reusável) +
  `key_id` (público, indexado). Dependency `api_key_scope`:
  1. parse do header (`Authorization: Bearer` ou `X-API-Key`)
  2. split prefixo → `key_id`
  3. `SELECT` por `key_id` + `revoked_at IS NULL`
  4. `verify` argon2id; falha → 401 estável
- Cache curto (TTL 30s) opcional para latência; invalidação no revoke (revogação < 1min — RN-020).
- **Confidence: HIGH** — argon2id já usado em auth (Phase 2).

### 4. Webhooks outbound HMAC + retry (REQ-043)
- Assinatura: `X-Jaxego-Signature: t=<unix_ts>,v1=<hex(hmac_sha256(secret, f"{t}.{raw_body}"))>`
  (esquema Stripe). `X-Jaxego-Event-Id: <ULID>` para anti-replay no receptor (janela 5 min).
- Disparo: a partir de `deliveries.service.transition` (ponto único de escrita de state, Phase 7),
  enfileira `webhook_events` row + job arq — **nunca** bloqueia a transição (try/except: falha de
  enqueue vira log+TD, não derruba a entrega).
- Retry backoff exato ADR-010: `[0, 30, 120, 600, 3600, 14400, 43200, 86400]` segundos (8). Job
  reagenda a si mesmo com `_defer_by` no próximo intervalo; resposta 2xx = sucesso; ≥8 falhas →
  `failed` + alerta.
- `mask payload`: serializer público reusa as regras de minimização de PII da Phase 9 (sem endereço
  pré-COLETADA, sem telefone, `public_token`/`reference_number`).
- **Confidence: MED** — o backoff self-rescheduling no arq precisa de teste de tempo controlado
  (LOW-1, vira task explícita — Regra 12).

### 5. Tela 22 (admin API keys) — frontend
- Rota lazy no shell admin de área. Reusa `jx-data-table` (Phase 6) e confirmação sensível.
- Criação exibe segredo **uma vez** (componente copy-once com aviso). Reusa tokens existentes.
- **Confidence: HIGH**.

## Security Baseline (Gate 4 — owasp-security)

> Fase com endpoints públicos autenticados + webhooks + segredo → baseline obrigatório.
> Skill consultada: `owasp-security` (api-input-validation, auth-and-session, A02/A07/A08/A10).

| # | Ameaça (STRIDE / OWASP) | Vetor | Mitigação nesta phase |
|---|---|---|---|
| TH-01 | **Broken auth** (A07) — API key vazada/forjada | header | key como argon2id hash, nunca em claro; segredo exibido 1×; 401 estável (latência constante, anti-enum); soft-revoke < 1min |
| TH-02 | **Injection** (A03) no body público | POST /v1/deliveries | Pydantic strict (`extra=forbid`), reuso da validação do service; sem SQL string-building (SQLAlchemy 2.x bound) |
| TH-03 | **IDOR / cross-area** (A01) | `merchant_external_ref`/`merchant_id` | resolução SEMPRE escopada à `area_id` da API key; loja de outra área → 404; sem vazamento de existência |
| TH-04 | **Replay de criação** | Idempotency-Key | persistência 24h; mesma key+body → mesma resposta; key+body divergente → 409 |
| TH-05 | **SSRF via webhook URL** (A10) | URL configurada pela área | validar URL no cadastro: só https, bloquear hosts privados/loopback/link-local/metadata (169.254.169.254), reusar guarda SSRF dos adapters (Phase 4 `integrations`) |
| TH-06 | **Webhook forjado no receptor** | — | assinatura HMAC-SHA256 + `t` (timestamp) + event-id; doc instrui janela 5 min anti-replay |
| TH-07 | **Timing attack** na verificação | — | `hmac.compare_digest` (nunca `==`) — já é o padrão do repo |
| TH-08 | **DoS / abuso** (A04) | flood na API pública | rate limit por API key (reuso ratelimit); 429 + Retry-After |
| TH-09 | **Segredo/PII em log** (A09) | logs de request/webhook | API key e secret NUNCA logados; payload de webhook minimiza PII (RN-013); campos proibidos já no config observability |
| TH-10 | **Webhook delivery infinita** | receptor 5xx | máximo 8 tentativas com backoff; depois `failed`+alerta (não retry eterno) |

**Decisões de auth herdadas:** ADR-005 (argon2id), ADR-010 (esquema da API pública). Nada de novo
PSP/secret fora de `settings`.

## LOW confidence → vira task (Regra 12)
- **LOW-1:** backoff self-rescheduling do job de webhook precisa de teste com tempo controlado
  (freeze/fake clock). → **Task explícita no PLAN** com critério de aceite (8 intervalos exatos).

## Skills aplicáveis
- `product/api-design-contracts` (contrato REST, idempotência, versionamento, RFC 7807)
- `owasp-security` (baseline acima — Gate 4)
- `quality/observability-production` (health de webhook, métricas de entrega/retry, rate limit)
- `domain/fastapi-production-patterns` (dependencies, routers, async)
- matriz UI mínima (tela 22) + `ux-advanced/data-tables-ux` + `br/ux-copywriting-ptbr`
- `domain/mysql-schema-design` (migration 0010, índices)
