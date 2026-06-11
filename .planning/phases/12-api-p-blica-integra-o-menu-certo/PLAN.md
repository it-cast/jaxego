# Phase 12: API pública + integração Menu Certo - PLAN

**Milestone:** MS-04 · **has_ui:** true (tela 22) · **integration_check:** true (round-trip Menu Certo simulado)
**Status:** Ready for execution · **Migration:** 0010 · **Date:** 2026-06-11 (autopilot)

## Goal
Expor a API pública para integradores: `POST /v1/deliveries` idempotente autenticado por API key
por área (REQ-041/042, RN-020), e webhooks outbound assinados (HMAC-SHA256) com anti-replay e retry
exato 8× (REQ-043). UI: tela 22 (admin de área gerencia keys + webhook). Reusa o `create_delivery`
service e as regras de minimização de PII já existentes.

## Skills Consultadas
- `product/api-design-contracts` — base das D-04/D-05: idempotência por header com cache 24h,
  erros RFC 7807, versionamento /v1/, contrato estável de request/response (ver RESEARCH §1/§2).
- `owasp-security` (api-input-validation, auth-and-session, A01/A02/A03/A07/A08/A10) — fonte do
  threat model abaixo (TH-01..TH-10); decide hash argon2id da key (D-01), 401 estável, anti-SSRF na
  URL de webhook (TH-05), `compare_digest` (TH-07). Gate 4 baseline em RESEARCH.md.
- `quality/observability-production` — D-07/D-09: health/métricas de entrega de webhook, contadores
  de retry, alerta em `failed`; campos PII proibidos em log (TH-09); rate limit observável (D-05).
- `domain/fastapi-production-patterns` — estrutura do módulo (dependencies `api_key_scope`
  espelhando `MerchantScopeDep`), async, commit no router.
- `domain/mysql-schema-design` — migration 0010: `api_keys`, `api_idempotency_keys`,
  `webhook_endpoints`, `webhook_deliveries`; índices por `key_id`/`(api_key_id, idempotency_key)`;
  FK RESTRICT; reversível (lição migrations 0006/0008).
- `product/component-library-governance` — tela 22 reusa jx-data-table/estados/confirmação; só
  `jx-secret-reveal` é novo (D-10).
- `quality/accessibility-pro` — modal foco-preso/Esc, aria-live no aviso de segredo, contraste AA
  nos 2 temas (UI-SPEC §a11y).
- `ux-advanced/design-tokens-system` + `ui-ux-pro-max` — UI-SPEC inteiro via tokens; zero hex.
- `ux-advanced/dark-mode-theming` (DEC-001) — tela 22 nos dois temas; tokens semânticos já têm dark.
- `ux-advanced/empty-states-polish` — empty states de keys e de histórico de webhook (UI-SPEC).
- `ux-advanced/data-tables-ux` — tabela de keys e de entregas de webhook (paginadas, status, ações).
- `br/ux-copywriting-ptbr` — copy pt-BR sem jargão (aviso de segredo, revogação) — UI-SPEC §copy.

## Skills Dispensadas (com justificativa)
- `domain/safe2pay-escrow-br` / `domain/saas-billing-canonical` — esta phase **não** toca billing
  (`has_payments: false`). Cobrança via API é da Phase 10 (já feita) e financeiro da Phase 15.
- `ux-advanced/payment-checkout-ux` / `trust-safety-ux` — sem checkout/onboarding nesta tela.
- `domain/monorepo-deploy-safety` / `domain/github-actions-ci` — flagged por keyword "deploy/CI" no
  loader, mas não há trabalho de deploy/CI nesta phase; isso é a Phase 14.
- `mobile/*` — sem superfície mobile (tela 22 é admin desktop).
- `ux-advanced/form-ux-mastery` / `quality/error-ux-patterns` — formulário mínimo (nome+escopos+URL);
  reuso dos padrões de erro já estabelecidos; não justifica a matriz completa de forms.

## Threat model (herdado do Security Baseline — RESEARCH.md §Security Baseline)
TH-01 auth (argon2id hash, 401 estável, revoke<1min) · TH-02 injection (Pydantic strict) ·
TH-03 IDOR cross-area (escopo por area_id → 404) · TH-04 replay criação (idempotência 24h / 409) ·
TH-05 SSRF webhook URL (https + bloqueio de host privado/metadata) · TH-06 webhook forjado (HMAC+ts+event-id) ·
TH-07 timing (`compare_digest`) · TH-08 DoS (rate limit + 429 Retry-After) · TH-09 PII/secret em log (nunca) ·
TH-10 retry infinito (máx 8 + alerta). **secure-phase valida estes na verificação.**

## Tech debt deste plano (Regra 11)
Consulta a `.planning/TECH-DEBT.md`: nenhuma TD com prazo/owner nesta phase. TDs do Safe2Pay
(TD-10-01..04) pertencem à Phase 15. Nenhuma TD nova esperada; se surgir, registrar com urgency_class.

## LOW confidence → tasks (Regra 12)
- **LOW-1 (RESEARCH §4):** backoff self-rescheduling do webhook. → **Task T-09** com critério de
  aceite: teste com clock controlado prova os 8 intervalos exatos `[0,30,120,600,3600,14400,43200,86400]s`
  e que a 8ª falha marca `failed` + emite alerta.

## Tasks (waves)

### Wave 1 — Schema + API keys (backend)
- **T-01** Migration 0010: `api_keys`, `api_idempotency_keys`, `webhook_endpoints`,
  `webhook_deliveries` (area-scoped, FK RESTRICT, índices, reversível). Teste de reversibilidade
  (`pytest -m mysql` upgrade→downgrade→upgrade).
- **T-02** Módulo `app/api_keys/` (model/schemas/repo/service): gerar (`jxg_<key_id>_<secret>`),
  hash argon2id, listar, revogar (soft `revoked_at`). Segredo retornado só na criação.
- **T-03** Dependency `api_key_scope` (parse `Authorization: Bearer`/`X-API-Key` → key_id → verify
  argon2id → injeta `area_id`+escopos; 401 estável; cache 30s invalidado no revoke).

### Wave 2 — Endpoint público idempotente + webhooks (backend)
- **T-04** `POST /v1/deliveries` público: resolve loja (`merchant_external_ref`/`merchant_id`)
  escopado à área (404 cross-area), `Idempotency-Key` **obrigatório**, chama `create_delivery`,
  grava snapshot 24h, replay→mesma resposta / body divergente→409. RFC 7807. Rate limit + 429.
- **T-05** Job arq purge de `api_idempotency_keys` expiradas (aware-UTC, idempotente).
- **T-06** Módulo webhooks outbound: assinatura `t=...,v1=hmac_sha256` + `X-Jaxego-Event-Id` ULID;
  serializer público com minimização de PII (reusa regras Phase 9).
- **T-07** Hook em `deliveries.service.transition`: enfileira `webhook_events` nas 6 transições
  (D-08), try/except não bloqueante.
- **T-08** Validação anti-SSRF da URL de webhook no cadastro (só https; bloquear loopback/privado/
  link-local/169.254.169.254 — reusa guarda dos adapters).
- **T-09** Job de entrega de webhook com backoff exato 8× + `failed`+alerta (LOW-1, teste com clock).
- **T-10** Endpoints admin de área para keys + webhook config (`/v1/admin/areas/{id}/api-keys`,
  `/.../webhook`), TOTP/RBAC admin de área, histórico de entregas paginado.

### Wave 3 — Frontend tela 22
- **T-11** `jx-secret-reveal` (segredo 1× + copiar + aviso, a11y) + stories.
- **T-12** Tela 22: lista de keys (jx-data-table), criar (modal + secret reveal), revogar
  (confirmação sensível), painel de webhook (URL+secret+eventos+histórico). Rota lazy admin. Zero hex.
- **T-13** Serviço Angular + signals para keys/webhook; estados empty/loading/error; testes.

### Wave 4 — Integration check + verificação (Gate 5)
- **T-14** `gsd-integration-checker`: round-trip simulado Menu Certo — cria entrega via API key,
  recebe webhook num receptor fake que valida `X-Jaxego-Signature` (janela 5 min) e confirma a
  sequência de retry exata; revogação efetiva < 1 min; Idempotency repetida → mesma resposta.

## Verificação (ROADMAP)
- Idempotency-Key repetida → mesma resposta (F-04 E1); 429 com Retry-After (E4); 401 estável (E2).
- Receptor fake valida `X-Jaxego-Signature` + janela 5 min; retry exato 0s/30s/2min/10min/1h/4h/12h/24h.
- Revogação de chave efetiva em < 1 min.
- Wireframe-contract da tela 22 coberto.
- `uv run pytest` (not-mysql) + `pytest -m mysql` migration 0010 + `ng test` verdes; `ruff` limpo.
- Gate 8 (senior-quality-bar): sem segredo em claro/log, sem IDOR, sem injection, auth definida.

## Parallel-hint
`module-split` (backend api_keys ∥ webhooks são arquivos disjuntos; frontend separado). Wave 1 antes
das demais (schema). Waves 2 e 3 podem paralelizar (arquivos disjuntos).
