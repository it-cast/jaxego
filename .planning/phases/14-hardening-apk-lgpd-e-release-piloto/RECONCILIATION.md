# Phase 14 — Reconciliação (prometido vs. real)

**Data:** 2026-06-11 (autopilot) · **Status:** sem gaps de código; pendências de release são checklist/UAT explícitos

| Prometido (PLAN) | Real | Evidência |
|---|---|---|
| Jobs LGPD: anonimização 12m + exclusão 30d (dados sintéticos) | ✓ | `app/workers/lifecycle.py` (`anonymize_inactive`/`delete_ephemeral`) + `tests/workers/test_lgpd.py` |
| Retenção legal preservada | ✓ | checagem por EscrowLedger/DirectPaymentConfirmation/PaymentDispute |
| Infra LLM (router + ai_usage_log) sem feature | ✓ | `app/ai/` (Protocol+Claude+Stub+Router) + migration 0012 (global) |
| Default Claude (opus-4-x/haiku), API key só em settings | ✓ | `app/ai/claude.py` + `app/core/config.py` (lazy import; Stub no M1) |
| Refino fallback ETA (timeout+circuit breaker, métrica) | ✓ | `app/deliveries/eta.py` (`EtaResolver`, `eta_source`) |
| CI: gates web (test/lint/build/zero-hex/lighthouse) + APK debug | ✓ | `.github/workflows/ci.yml` (jobs `web`, `apk`) |
| Validação de performance (orçamento + relatório) | ✓ (runtime → CI/checklist) | `PERF-REPORT.md` + TD-14-03 |
| APK Capacitor (config + CI + checklist UAT) | ✓ (debug; assinado → UAT) | `ci.yml` job `apk` + `capacitor.config.ts` + TD-14-04 |
| Checklist de release com BLOCKERS | ✓ | `RELEASE-CHECKLIST.md` (B-01 contrato Safe2Pay, B-02 secrets, B-03 migrations, B-04 seed admin) |
| Zero hex / suíte verde / lint | ✓ | frontend 177 + zero hex (3 exceções técnicas); backend 472 (1 flaky pré-existente); ruff limpo |

## Desvios / TD
- **TD-14-01** SDK anthropic lazy (infra-only) · **TD-14-02** ETA rodoviário não consumido ainda ·
  **TD-14-03** perf runtime (anexar Lighthouse+p95 de CI) · **TD-14-04** APK assinado = UAT humano.
- `ai_usage_log` sem area_id (ADR-001, global) — instrução literal.

## Gaps abertos
Nenhum de código. Pendências de **release** (não de implementação) estão explícitas no
RELEASE-CHECKLIST.md como BLOCKERS/WARNINGS/UAT — em especial **B-01 (contrato Safe2Pay)** que gate o
go-live de cartão/PIX (DEC-004), e o `pytest -m mysql` das migrations contra DB de produção/staging.
