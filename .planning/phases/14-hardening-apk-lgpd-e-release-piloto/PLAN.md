# Phase 14: Hardening, APK, LGPD e release piloto - PLAN

**Milestone:** MS-05 · **has_ui:** true (auditoria) · **has_ai:** true (infra) · **has_payments:** true (regressão)
**is_pre_release: true** · **integration_check:** true (smoke end-to-end) · **Migration:** 0012
**Status:** Ready for execution · **Date:** 2026-06-11 (autopilot)
**Depende de:** [12, 13] ✓

## Goal
Endurecer e preparar o piloto para deploy: jobs LGPD (anonimização 12m + exclusão 30d), infra de LLM
(router + ai_usage_log, **sem feature de IA**), refino de fallback de ETA, APK Capacitor (config+CI+
checklist), validação de performance, auditoria pré-release (squad-audit + release-auditor). Escopo de
pagamentos no deploy = Phase 10 (cartão/PIX live, assumindo contrato — DEC-004); back-office financeiro
fica na Phase 15.

## Skills Consultadas
- `br/lgpd-compliance` — D-01/D-02: anonimização 12m + exclusão 30d, retenção legal preservada, dados
  sintéticos no teste; campos PII proibidos.
- `domain/llm-integration-patterns` — D-03: router Protocol+adapter (Claude default opus-4-x/haiku) +
  Stub + `ai_usage_log` sem PII; infra plugável sem feature no M1.
- `owasp-security` (auditoria completa) — Security Baseline TH-01..TH-08 (secret/keystore, PII, migrations,
  regressão auth/IDOR/injection). Gate 4 + Gate 8.
- `quality/performance-web-vitals` — D-06: orçamento LCP/INP/CLS/bundle + p95 sob carga (relatório → TD).
- `quality/accessibility-pro` — auditoria axe das telas-chave nos 2 temas (UI-SPEC §2).
- `quality/observability-production` — métrica `eta_source` (D-04), health checks, cobertura de log; alertas.
- `domain/github-actions-ci` — D-08: gates de CI (test+lint+axe+bundlesize+lighthouse) + build APK debug.
- `domain/monorepo-deploy-safety` — D-07: checklist de release, secrets/migrations/env, ordem de deploy.
- `product/visual-regression-testing` — UI-SPEC §1: snapshots claro+escuro das telas críticas.
- `webapp-testing` — smoke end-to-end das superfícies (integration_check).
- `mobile/offline-first` + `mobile/push-notifications-architecture` — validação do APK (checklist UAT).
- `ui-ux-pro-max` — web-design-audit (anti-AI-slop, zero hex em todo apps/web).
- `ux-advanced/design-tokens-system` — verificação de conformidade de tokens (zero hex).
- `domain/mysql-schema-design` — migration 0012 (`ai_usage_log`); reversível.

## Skills Dispensadas (com justificativa)
- `domain/safe2pay-escrow-br`/`saas-billing-canonical`/`payment-checkout-ux` — sem novo código de
  billing; pagamentos aqui são **regressão** do que a Phase 10 já entregou. O back-office financeiro é
  a Phase 15. O go-live do cartão/PIX é sinalizado no checklist (dependente do contrato).
- `br/brazilian-forms`/`form-ux-mastery` — sem formulários novos (phase de hardening).
- `ux-advanced/*` específicos de feature (checkout/chat/upload) — não há telas novas.

## Threat model (herdado — RESEARCH §Security Baseline)
TH-01 secret/keystore (settings, scan) · TH-02 PII retida (jobs LGPD) · TH-03 PII em ai_usage_log (sem) ·
TH-04 migrations aplicáveis (release-auditor) · TH-05 health/observability (auditar) · TH-06 regressão
auth/IDOR/injection (suíte + owasp) · TH-07 deploy cartão/PIX sem contrato (checklist bloqueia) ·
TH-08 permissões do APK. **secure-phase + squad-audit + release-auditor validam.**

## Tech debt deste plano (Regra 11 — TDs pre_launch vencendo nesta phase)
Consulta a `.planning/TECH-DEBT.md` filtrando `pre_launch_*`:
- **TD-10-01..04** (Safe2Pay cutover) — sinalizadas no checklist de release como pré-requisito de
  go-live de cartão/PIX (dependem do contrato — DEC-003/004). Não resolvidas aqui (são da Phase 15/
  contrato); o checklist as torna visíveis no deploy.
- **TD-12-01** (path API pública), **TD-13-01** (revenue share %) — revisar antes do go-live (entram
  no checklist de release).
- TDs `pre_launch` de phases anteriores (verificação ao vivo MySQL das migrations 0004/0005/0006/0008/
  0010/0011) — consolidar num passo de smoke `pytest -m mysql` no checklist.

## LOW confidence → tasks (Regra 12)
- **LOW-1:** build de APK no CI → **T-06** entrega config+workflow; validação em runner/device = TD + checklist.
- **LOW-2:** p95 sob carga → **T-07** relatório; violações → TD.

## Tasks (waves)

### Wave 1 — LGPD + LLM infra + ETA (backend)
- **T-01** Jobs LGPD `anonymize_inactive` (12m) + `delete_ephemeral` (30d) em `app/workers/lifecycle.py`
  (aware-UTC, idempotente, auditado). Testes com **dados sintéticos**. Respeita retenção legal.
- **T-02** Módulo `app/ai/`: `LLMProvider` Protocol + `ClaudeAdapter` (default opus-4-x/haiku) + Stub +
  `LLMRouter` (config-driven) + `ai_usage_log` (migration 0012, global, sem PII). **Sem feature/endpoint** no M1.
- **T-03** Refino fallback ETA: OSRM timeout+circuit-breaker → estimativa mediana; métrica `eta_source`.

### Wave 2 — Release infra (CI / APK / performance)
- **T-04** CI (`.github/workflows/ci.yml`): gates test+lint+axe+bundlesize+lighthouse; ordem segura
  (monorepo-deploy-safety). Garantir verdes.
- **T-05** Performance: rodar lighthouse + bundlesize; load test sintético p95 criar-entrega/aceitar;
  relatório em `phases/14-.../PERF-REPORT.md`; violações → TD.
- **T-06** APK: completar `capacitor.config.ts` Android + workflow de build APK debug; documentar
  checklist UAT humano (câmera/GPS/push em device); registrar TD do release assinado.

### Wave 3 — Auditoria pré-release + checklist de deploy
- **T-07** Visual regression + axe das telas-chave (claro+escuro); confirmar **zero hex** em apps/web.
- **T-08** Smoke end-to-end (`webapp-testing` + integration_check) das superfícies principais.
- **T-09** **Checklist de release** (`phases/14-.../RELEASE-CHECKLIST.md`): secrets, migrations
  (`alembic heads` + `pytest -m mysql`), env vars, health checks, **TD-10-01..04 (contrato Safe2Pay)
  como BLOCKER explícito de go-live de cartão/PIX**, APK debug. Bloqueia deploy se BLOCKER aberto.

## Verificação (ROADMAP)
- APK gerado no CI (debug), instala e exerce câmera/GPS/push em device real (checklist UAT humano).
- Job de anonimização 12m + exclusão 30d testados com dados sintéticos.
- p95 < 200ms em criar-entrega/aceitar-oferta sob carga sintética; LCP < 2500ms 4G.
- Suíte completa + lint verdes; **zero FAIL-BLOCK do Senior Quality Bar** (Gate 8).
- squad-audit (perf/a11y/i18n/observability) + release-auditor (deploy-safety) sem CRITICAL/BLOCKER
  não-tratado.

## Parallel-hint
`module-split` — LGPD ∥ LLM ∥ ETA são disjuntos (Wave 1). Wave 2/3 dependem do código pronto.
