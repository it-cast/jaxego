# Phase 12: API pública + integração Menu Certo - Context

**Gathered:** 2026-06-11 (modo --auto, autopilot)
**Status:** Ready for planning

<domain>
## Phase Boundary

Expor a API pública para integradores (Menu Certo em primeiro lugar): `POST /v1/deliveries`
idempotente autenticado por **API key por área** (RN-020), e **webhooks outbound** assinados
(HMAC-SHA256) com anti-replay e retry exponencial para notificar o integrador de mudanças de
estado da entrega. Inclui a tela 22 (admin de área gerencia API keys). **Fora de escopo:** lógica
de criação/máquina de estados da entrega (já entregue na Phase 7), pagamentos (Phase 10), e o
back-office financeiro (Phase 15).
</domain>

<decisions>
## Implementation Decisions

### Autenticação da API pública (RN-020)
- **D-01:** API key **por área** (não por loja). Formato `jxg_<area_prefix>_<random>`; armazenada
  como **hash** (argon2id, reusando `app.core.security`) — nunca em texto puro. O segredo só é
  exibido **uma vez** na criação (tela 22). Lookup por `key_id` (prefixo público não-secreto).
- **D-02:** Header `Authorization: Bearer jxg_...` OU `X-API-Key: jxg_...` (aceitar ambos; doc
  recomenda `Authorization`). Dependency `ApiKeyScopeDep` resolve `area_id` + escopos e injeta no
  request, espelhando `MerchantScopeDep` das deliveries. Chave inválida/revogada → 401 estável
  (mesma latência, anti-enumeração).
- **D-03:** A criação via API pública precisa de uma **loja-alvo** dentro da área. O integrador
  passa `merchant_external_ref` (o ID da loja no sistema do integrador) OU `merchant_id`. A área
  mapeia ref→merchant. Sem loja resolvível → 422 com `type` RFC 7807 claro.

### Idempotência (REQ-041, F-04 E1)
- **D-04:** `Idempotency-Key` header **obrigatório** na criação pública (diferente do opcional no
  endpoint interno). Cache de resposta por **24h** (ADR-010) chaveado por
  `(api_key_id, idempotency_key)`. Replay da mesma key → **mesma resposta** (mesmo status/body),
  sem criar segunda entrega. Tabela `api_idempotency_keys` (request_hash + response snapshot +
  expires_at). Request com mesma key mas body divergente → 409 (`key reuse with different body`).

### Rate limiting e erros (F-04 E2/E4)
- **D-05:** Rate limit por API key (reusar `app.core.ratelimit`). Estouro → **429 com
  `Retry-After`** (RFC 7807 + header). 401 estável para chave inválida (E2). Todos os erros em
  formato RFC 7807 (DRV-003) — `type`, `title`, `status`, `detail`, `instance`.

### Webhooks outbound (REQ-043, F-04)
- **D-06:** Eventos de mudança de estado da entrega geram webhooks para a URL configurada por área.
  Assinatura `X-Jaxego-Signature: t=<ts>,v1=<hmac_sha256(secret, "<ts>.<body>")>` (esquema estilo
  Stripe) + `X-Jaxego-Event-Id` (ULID, anti-replay no receptor — janela de 5 min). Secret de
  webhook por área (rotacionável).
- **D-07:** Entrega via **job arq** (nunca inline no request de criação). Retry com backoff
  **exato** ADR-010: `0s, 30s, 2min, 10min, 1h, 4h, 12h, 24h` (8 tentativas). Após esgotar →
  `failed` + alerta de observabilidade. Cada tentativa registrada em `webhook_deliveries`
  (status_code, tentativa, próximo retry). Resposta 2xx do receptor = sucesso.
- **D-08:** Eventos cobertos: `delivery.created`, `delivery.accepted`, `delivery.collected`,
  `delivery.delivered`, `delivery.finalized`, `delivery.canceled` (mapeados da máquina de 7 estados
  da Phase 7). Payload **minimiza PII** (RN-013): sem endereço completo antes de COLETADA, sem
  telefone do destinatário; usa `public_token` e `reference_number`.

### Revogação (tela 22)
- **D-09:** Revogação de API key efetiva em **< 1 min** (RN-020 / verificação). Como o lookup vai ao
  DB a cada request (com cache curto de 30s no máximo), revogação propaga rápido; cache invalidado
  no revoke. Soft-revoke (`revoked_at`), nunca delete (auditoria).

### UI tela 22 (admin de área)
- **D-10:** Tela 22 = lista de API keys da área (jx-data-table), criar (mostra segredo uma vez com
  copy + aviso "não será exibido de novo"), revogar (confirmação), e configurar webhook (URL +
  secret + eventos + ver últimas entregas/falhas). Reusa componentes governados existentes
  (jx-data-table, jx-empty-state, confirmação sensível).

### Claude's Discretion
- Estrutura exata das tabelas (índices), nomes internos de funções, paginação por cursor vs offset
  no histórico de webhooks, layout fino da tela 22.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisão arquitetural e fluxo
- `.planning/DECISIONS.md` — ADR-010 (API key por área + Idempotency-Key cache 24h + webhooks
  HMAC-SHA256 anti-replay + retry 8×; rejeitados gRPC/GraphQL/WebSocket/polling/OAuth2 v2) ·
  DRV-003 (versionamento /v1/, RFC 7807, paginação cursor, idempotência por header)
- `.planning/ROADMAP.md` — Phase 12 (REQs 041/042/043, verificações automatizadas, wireframe 22)
- `projeto/regras-negocio/fluxos.md:72-86` — F-04 (fluxo da API pública, exceções E1–E4)
- `projeto/docs-externos/integracoes.md:40-51` — contrato de integração Menu Certo
- RN-020 — API keys e escopo

### Padrões de código a reusar (já no repo)
- `apps/api/app/deliveries/router.py` — POST create + `Idempotency-Key` + `merchant_scope` (espelhar)
- `apps/api/app/deliveries/dependencies.py` — `MerchantScopeDep` (modelo para `ApiKeyScopeDep`)
- `apps/api/app/payments/webhooks_router.py` — HMAC `compare_digest` (inbound; inverter p/ outbound)
- `apps/api/app/core/security.py` — argon2id (hash de API key) · `app/core/ratelimit.py` · `app/core/config.py`
- `apps/api/app/deliveries/service.py` — `create_delivery` (a API pública chama o MESMO service)

### Segurança
- skill `owasp-security` (api-input-validation, HMAC, anti-replay) — Gate 4
- skill `product/api-design-contracts` · `quality/observability-production` (health de webhook, rate limit)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `service.create_delivery(...)`: a API pública é um **adaptador de auth** na frente do mesmo
  service de criação — zero duplicação da máquina de estados/estimativa/limite de plano.
- `Idempotency-Key` já é aceito no router interno de deliveries — o padrão de header existe;
  a diferença é a persistência 24h (cache de resposta) que é nova nesta phase.
- `_verify_hmac` em payments/webhooks_router mostra o estilo `compare_digest` — para outbound,
  geramos a assinatura com o mesmo `hmac.new(secret, ..., sha256)`.
- `app.core.ratelimit.RateLimitedError` + limiter — reusar para o limite por API key.
- Workers arq (`app/workers/`) — padrão de job idempotente aware-UTC para a entrega de webhook.

### Established Patterns
- Módulo = `model.py` + `schemas.py` + `repo.py` + `service.py` + `router.py` + `dependencies.py`.
- `commit()` no router (não no service). Erros RFC 7807. PII fora de log. Soft-delete em domínio.
- Migrations Alembic sequenciais reversíveis (próxima: **0010**); FK RESTRICT em transacionais.

### Integration Points
- Montar novos routers em `app/api/v1/router.py` (bloco "Phase 12").
- Webhook outbound disparado a partir do mesmo ponto que muda `delivery.state`
  (`deliveries.service.transition`) — enfileira evento, nunca bloqueia a transição.
- Tela 22 entra no shell admin de área (apps/web), reusando design system.
</code_context>

<specifics>
## Specific Ideas
- Assinatura de webhook estilo Stripe (`t=...,v1=...`) — formato conhecido por integradores, fácil
  de validar no Menu Certo.
- 401 deve ter latência estável (não revelar se a key existe) — anti-enumeração consistente com o
  resto do sistema (Phases 4/5/9).
</specifics>

<deferred>
## Deferred Ideas
- OAuth2 para integradores — explicitamente rejeitado (ADR-010, v2).
- Webhooks para eventos financeiros (cobrança/estorno) — Phase 15 (back-office financeiro).
- Portal self-service de developer/API docs interativo — fora do M1 (backlog).
</deferred>

---

*Phase: 12-api-p-blica-integra-o-menu-certo*
*Context gathered: 2026-06-11*
