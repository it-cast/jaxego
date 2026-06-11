# Phase 14: Hardening, APK, LGPD e release piloto - Research

**Status:** Ready for planning · **Date:** 2026-06-11 (autopilot) · **is_pre_release: true**

## Achados técnicos

### 1. Jobs LGPD (REQ-048)
- Molde: `app/workers/lifecycle.py` (`purge_locations`). Novos cron jobs:
  - `anonymize_inactive` — entidades (couriers/recipients/users) inativas há **12 meses**: substitui
    PII (nome→placeholder, cpf/cpf_hash→tombstone, phone→null) preservando agregados; irreversível,
    auditado. **Nunca** toca registros com retenção legal (fiscal/financeiro).
  - `delete_ephemeral` — rascunhos/dados não-consumados há **30 dias** (ex.: signups abandonados, OTPs
    expirados, idempotency keys vencidas) hard-delete.
- Idempotente, aware-UTC, best-effort por linha. **Teste com dados sintéticos** (factory), nunca reais.
- **Confidence: HIGH** (molde existe).

### 2. Infra LLM (REQ-053) — só trilho
- `app/ai/`: `Protocol` `LLMProvider` + `ClaudeAdapter` (anthropic SDK; default claude-opus-4-x p/
  raciocínio, claude-haiku p/ alto volume) + `StubProvider` (dev/test). `LLMRouter` escolhe provider/
  modelo por tarefa via config. Tabela `ai_usage_log` (**global**, ADR-001): provider, model, task,
  input/output tokens, cost_cents, latency_ms, request_id, ok/erro — **sem PII, sem prompt cru com PII**.
- **Nenhum endpoint/feature de IA no M1** — só a infra plugável. Segue `domain/llm-integration-patterns`.
- API key do provider só em `settings`/secret, nunca em log/código. **Confidence: HIGH**.

### 3. Refino ETA/OSRM (REQ-054)
- OSRM primário com timeout + circuit breaker → fallback haversine/estimativa mediana (Phase 7/9).
  Nunca bloqueia criação. Métrica `eta_source` (osrm|fallback). **Confidence: HIGH** (refino, não algoritmo novo).

### 4. APK Capacitor (REQ-051)
- `capacitor.config.ts` existe. Completar config Android, `npx cap add android` no CI, build **debug**
  no pipeline. Release assinado (keystore) + exercício de câmera/GPS/push em device = **checklist UAT
  humano** (não automatizável → vira itens de checklist, não código). **Confidence: MED** (CI de APK
  no Windows local não é validável aqui — vira TD/checklist).

### 5. Performance (REQ-050)
- Rodar `lighthouserc.json` + bundlesize (config já existe). Load test sintético de criar-entrega/
  aceitar-oferta para p95. Resultado = relatório; violação = TD com urgency_class. **Confidence: MED**.

### 6. Release-safety (deploy)
- `gsd-release-auditor` no fechamento: secrets, migrations aplicáveis, health checks, env vars,
  keystore/plist. **Sinalizar explicitamente** que o go-live de cartão/PIX (Phase 10) depende de
  TD-10-01..04 (contrato Safe2Pay) — DEC-003/004. Código pronto atrás de Stub.

## Security Baseline (Gate 4 — owasp-security auditoria completa)

> Phase de release → auditoria abrangente, não só do novo código.

| # | Ameaça / Área | Mitigação / verificação |
|---|---|---|
| TH-01 | Secret/keystore/API key de LLM exposto (A02) | tudo em settings/secret; scan no release-auditor; nunca em log/git |
| TH-02 | PII retida além do necessário (LGPD) | jobs de anonimização 12m + exclusão 30d (REQ-048); locations 24h (Phase 9) |
| TH-03 | PII em ai_usage_log ou prompt | `ai_usage_log` sem PII; router não loga prompt com dado pessoal |
| TH-04 | Migrations não-aplicadas em prod | release-auditor confere `alembic heads`/sequência; smoke de upgrade |
| TH-05 | Endpoints sem health/observability | health check + campos de log obrigatórios já no config; auditar cobertura |
| TH-06 | Regressão de auth/IDOR/injection (A01/A03/A07) | suíte completa + owasp audit de todos os módulos (Gate 8 senior-quality-bar) |
| TH-07 | Deploy do cartão/PIX sem contrato | checklist bloqueia: TD-10-01..04 sinalizados como pré-requisito de go-live |
| TH-08 | APK com permissões excessivas | revisar manifesto Android (só câmera/GPS/push/internet necessárias) |

## LOW confidence → tasks (Regra 12)
- **LOW-1:** build de APK no CI (Windows local não valida) → **Task** que entrega config + workflow CI
  e registra **TD** (validação em runner real / device é checklist UAT humano).
- **LOW-2:** p95 sob carga sintética depende de ambiente → **Task** de relatório; violações viram TD.

## Skills aplicáveis
- `br/lgpd-compliance` · `owasp-security` (auditoria completa) · `quality/performance-web-vitals` ·
  `quality/accessibility-pro` · `quality/observability-production` · `domain/llm-integration-patterns` ·
  `domain/github-actions-ci` · `domain/monorepo-deploy-safety` · `webapp-testing` ·
  `product/visual-regression-testing` · `mobile/offline-first` · `mobile/push-notifications-architecture` · `ui-ux-pro-max`
