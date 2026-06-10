---
phase: 04-cadastro-e-ativa-o-de-loja
plan: 01
subsystem: api
tags: [merchants, plans, signup, otp, ssrf, adapters, validate-docbr, httpx, arq, angular, wizard, brazilian-forms, lgpd]

# Dependency graph
requires:
  - phase: 02-core-auth-multiarea
    provides: users + argon2id + anti-enumeração (verify_dummy) + AreaScopedMixin + audit_log + worker arq + aware-UTC (db/mixins) + RFC-7807
  - phase: 03-shell-frontend-design-system
    provides: design system (21 vars semânticas claro/dark), componentes de estado (empty/error/warn/skeleton), login, ThemeService
provides:
  - "Backend F-01: /v1/merchants/signup (E1–E4), /v1/merchants/{id}/confirm-phone, /confirm-email, /v1/plans, /v1/interest"
  - "Entidades merchants/merchant_users/subscription_plans/merchant_subscriptions (migration 0003)"
  - "Máquina de estados do merchant (pending_payment/pending_validation/active/suspended) com transições auditadas"
  - "Adapters Receita/SMS/SES/geocoding (Protocol + httpx + Stub) com guarda SSRF"
  - "OTP de SMS aware-UTC + job arq de revalidação Receita (retry 6/6/12/24h)"
  - "Seed idempotente (Pádua + 4 planos + admins)"
  - "Frontend: wizard de cadastro (tela 02), seleção de plano (tela 16), estado vazio + onboarding"
affects: [05-cadastro-entregador, 07-criacao-de-entregas, 10-checkout-safe2pay]

# Tech tracking
tech-stack:
  added: [validate-docbr 2.0.0 (CPF/CNPJ + alfanumérico jul/2026), httpx promovido a runtime]
  patterns: [adapter Protocol+httpx+Stub selecionado por environment, SSRF assert_safe_url (allowlist + rejeita IP privado), state machine explícita com audit, OTP/retry aware-UTC, seed idempotente upsert por chave natural, planos data-driven do SEED (DRV-009), wizard com persistência parcial sem senha]

key-files:
  created: [apps/api/app/merchants/{models,schemas,service,state_machine,otp,router}.py, apps/api/app/plans/{models,service,router}.py, apps/api/app/integrations/{base,http,receita,receita_stub,sms,sms_stub,email,email_stub,geocoding,geocoding_stub,factory}.py, apps/api/app/workers/revalidate.py, apps/api/app/core/ratelimit.py, apps/api/alembic/versions/0003_merchants_plans.py, apps/api/tools/seed.py, apps/web/src/shared/components/{wizard-stepper,field,plan-card}/*, apps/web/src/features/loja/cadastro/*, apps/web/src/features/loja/plano/*, apps/web/src/features/loja/dashboard/onboarding-hint.component.ts]
  modified: [apps/api/app/api/v1/router.py, apps/api/app/core/{config,logging}.py, .planning/config.json (denylist+phone), apps/web/src/app/app.routes.ts, apps/web/src/features/loja/inicio.page.ts, .env.example]

key-decisions:
  - "Adapters externos como Protocol+httpx+Stub; factory retorna Stub em {dev,test} — testes nunca tocam a rede (Gate 5)"
  - "validate-docbr 2.0.0 valida CNPJ alfanumérico (jul/2026) — sem troca de lib (LOW A7 resolvido)"
  - "Anti-enumeração: colisão CNPJ/telefone/e-mail → mensagem única + verify_dummy (tempo ~constante), reusando padrão da Phase 2"
  - "Resolução de área por bounding box (area.config bbox, default Pádua); polígono preciso fica para fase de mapas"
  - "Rate limit de signup in-process (sliding window) — Redis distribuído é upgrade futuro"

patterns-established:
  - "SSRF guard: assert_safe_url(allowlist) rejeita host fora da allowlist + IP privado/link-local/loopback, follow_redirects=False"
  - "Máscara de PII em log (mask_email/phone/document) + denylist central com phone/document"
  - "Planos como SEED editável (DRV-009): valores no PLAN_SEEDS, GET /v1/plans projeta do banco, zero hardcode no front"

requirements-completed: [REQ-006, REQ-008, REQ-009]

# Metrics
duration: ~3h
completed: 2026-06-10
---

# Phase 4 Plan 01: Cadastro e ativação de loja Summary

**Fluxo F-01 de cadastro de loja end-to-end no caminho Free com as 4 exceções (CNPJ inativo, colisão anti-enumeração, plano pago→pending_payment, Receita fora→pending_validation), adapters externos atrás de Protocol+Stub com guarda SSRF, OTP/job aware-UTC, seed idempotente e wizard Angular tela 02 + seleção de plano data-driven.**

## Performance

- **Duration:** ~3h
- **Started:** 2026-06-10
- **Completed:** 2026-06-10
- **Tasks:** 15 (T-00..T-14)
- **Files modified:** ~55 criados/modificados

## Accomplishments

- **Backend F-01 completo:** signup orquestra E1 (CNPJ inativo → bloqueio), E2 (colisão → mensagem única anti-enumeração com `verify_dummy` em tempo ~constante), E3 (plano pago → `pending_payment` usando Free ativo), E4 (Receita down → `pending_validation` + job de retry enfileirado).
- **4 adapters externos** (Receita minhareceita+BrasilAPI, SMS Zenvia→Twilio, SES, geocoding Nominatim) como `Protocol` + impl `httpx` + `Stub`, com `assert_safe_url` (SSRF A10) e factory que retorna Stub em dev/test — a suíte nunca toca a rede (Gate 5).
- **Máquina de estados do merchant** com transições válidas auditadas no `audit_log` (RN-012), OTP de SMS e janelas de retry (6/6/12/24h) em aware UTC (TD-010).
- **Seed idempotente** (`tools/seed.py`): Pádua + 4 planos (valores do SEED, DRV-009, Free imutável) + admin de plataforma + admin de área; rodar 2x não duplica.
- **Frontend:** wizard tela 02 (stepper de 4 passos, máscaras BR CNPJ/CPF/telefone E.164, CEP via ViaCEP, validação inline no blur, persistência parcial em sessionStorage SEM senha, E1/E2 via `jx-error-state`, consentimento LGPD), estado vazio "Ainda não chegamos aí" com captura de interesse, seleção de plano (tela 16) data-driven do `GET /v1/plans` sem dark pattern, banners pending_* (E3/E4) + onboarding hint. Zero hex hardcoded; dark mode em tudo (DEC-001).

## Task Commits

1. **T-00: scaffolds RED + deps** — `4513df6` (test)
2. **T-01: models + migration 0003** — `375f4cf` (feat)
3. **T-05: adapters + SSRF guard** — `ee27584` (feat)
4. **T-02/03/04: contrato + service E1–E4 + OTP** — `69143c0` (feat)
5. **T-13: spike fixtures + TD-014/015** — `e8c76ef` (test)
6. **T-07: job arq revalidate_receita** — `444f367` (feat)
7. **T-08: seed idempotente + .env.example** — `a73c657` (feat)
8. **T-06/T-14: PII fora de log + acceptance MySQL + suíte verde** — `8597614` (test)
9. **T-09: componentes governados (stepper/field/plan-card)** — `37a293a` (feat)
10. **T-10/11/12: wizard + plano + pending/onboarding** — `d66c596` (feat)

**Plan metadata:** (este commit) docs(04): EXECUTION-LOG + SUMMARY + STATE/ROADMAP

## Files Created/Modified

Ver frontmatter `key-files`. Destaques:
- `apps/api/app/merchants/service.py` — orquestração F-01 (E1–E4), anti-enumeração, decisão de plano, audit.
- `apps/api/app/integrations/http.py` — `assert_safe_url` (SSRF), cliente httpx sem redirect.
- `apps/api/alembic/versions/0003_merchants_plans.py` — 4 tabelas, UNIQUE composto `(account_type, document)` RN-011.
- `apps/api/tools/seed.py` — seed idempotente.
- `apps/web/src/features/loja/cadastro/cadastro.page.ts` — wizard de 4 passos.
- `apps/web/src/shared/components/plan-card/plan-card.component.ts` — card data-driven (DRV-009).

## Decisions Made

- **Adapters via Stub em {dev,test}:** desacopla a suíte da rede; contratos validados por `test_contracts` contra fixtures (Gate 5).
- **validate-docbr 2.0.0 já suporta CNPJ alfanumérico** (verificado: `12ABC34501DE35` válido, dígito adulterado rejeitado) — nenhuma troca de lib necessária.
- **Resolução de área por bbox** em `area.config` (default Pádua) — suficiente para cobertura vs. estado-vazio; polígono preciso fica para a fase de mapas.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rate limiter in-process criado para o signup**
- **Found during:** T-02 (contrato/router)
- **Issue:** O threat model (TH-07) exige rate limit no `/v1/merchants/signup`, mas não havia limiter no projeto.
- **Fix:** `app/core/ratelimit.py` (sliding window por IP, aware UTC) + dependency no router; limiter distribuído (Redis) documentado como upgrade futuro.
- **Files modified:** apps/api/app/core/ratelimit.py, apps/api/app/merchants/router.py
- **Verification:** fixture autouse reseta o limiter entre testes; signup 5/min/IP.
- **Committed in:** `69143c0`

**2. [Rule 2 - Missing Critical] Máscara de PII em log antecipada (parte de T-06)**
- **Found during:** T-03 (service)
- **Issue:** O service audita o signup; sem máscara, o hint de e-mail/telefone vazaria PII (TH-06/LGPD).
- **Fix:** `mask_email`/`mask_phone`/`mask_document` em `core/logging.py` + `phone`/`document` na denylist do `config.json`.
- **Files modified:** apps/api/app/core/logging.py, .planning/config.json
- **Verification:** `test_pii_logging` confirma que CNPJ/telefone/e-mail não aparecem em log.
- **Committed in:** `69143c0` (denylist) / `8597614` (teste)

**3. [Decisão de caminho] `.env.example` na raiz + apps/api**
- **Found during:** T-08
- **Issue:** O PLAN pede `apps/api/.env.example`; o repo já tinha `.env.example` na raiz (lido por settings via cwd).
- **Fix:** mantidos os DOIS sincronizados (raiz canônica + cópia em `apps/api` conforme plano/README).
- **Committed in:** `a73c657`

---

**Total deviations:** 3 (1 blocking, 1 missing-critical, 1 decisão de caminho)
**Impact on plan:** Todos necessários para correção/segurança (rate limit e PII estão no threat model). Sem scope creep.

## Issues Encountered

- **FastAPI 204 com response body:** o handler `confirm-email` retornava `None` com `status_code=204`, que o FastAPI rejeita. Resolvido com `response_class=Response` e retorno explícito de `Response(204)`.
- **Fixtures de stub não visíveis entre conftests irmãos:** as fixtures de geocoding foram movidas para o `tests/conftest.py` raiz para ficarem disponíveis em `tests/merchants/`.
- **Tipagem Literal do status:** `SignupResult.status` tipado como `Literal[...]` + `cast` para alinhar com o `response_model` (basedpyright limpo).

## User Setup Required

None bloqueante para dev/test (adapters em Stub). Em staging/production: preencher segredos de integração em env (`RECEITA_*`, `SMS_*`, `SES_*`, `GEOCODING_*`) conforme `.env.example`; nenhum segredo é commitado.

## Next Phase Readiness

- Entidades de loja, planos e o padrão de adapter+SSRF ficam prontos para a Phase 5 (entregador) e Phase 7 (entregas).
- **Verificação ao vivo pendente (MySQL real):** aplicar migration 0003, rodar `tools/seed.py` 2x (idempotência), `pytest -m mysql` (UNIQUE composto + append-only) e cadastro E1–E4 contra MySQL. Ver `EXECUTION-LOG.md` para os comandos.
- TD-014 (geocoding público rate limit) e TD-015 (callback SMS síncrono) registradas em TECH-DEBT.md.

## Self-Check: PASSED

- Todos os 9 arquivos-chave verificados existem em disco.
- Todos os 10 hashes de commit de task verificados existem no histórico git.
- Backend: ruff/format/basedpyright limpos; 112 passed / 4 deselected (@mysql).
- Frontend: build OK (158.62 kB transfer), lint OK, 33 testes verdes, 0 hex hardcoded.

---
*Phase: 04-cadastro-e-ativa-o-de-loja*
*Completed: 2026-06-10*
