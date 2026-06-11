# Phase 14: Hardening, APK, LGPD e release piloto - Context

**Gathered:** 2026-06-11 (modo --auto, autopilot)
**Status:** Ready for planning
**is_pre_release: true** — esta é a phase de **deploy do piloto** (Pádua).

<domain>
## Phase Boundary

Endurecer o sistema para o piloto e prepará-lo para deploy: (a) **jobs LGPD** de anonimização (12
meses) e exclusão (30 dias) sobre dados sintéticos (REQ-048); (b) **infra de LLM** — router multi-
provider + `ai_usage_log` (REQ-053, **infra apenas**, sem feature de IA no M1); (c) **refino dos
fallbacks de ETA/OSRM** (REQ-054); (d) **APK Capacitor** Android (REQ-051) — config + CI + checklist
UAT humano; (e) **validação de performance** p95 < 200ms / LCP < 2500ms (REQ-050); (f) **auditoria
pré-release** (squad-audit: perf/a11y/i18n/observability + release-auditor de deploy-safety).
**Escopo de pagamentos no deploy (DEC-004):** Phase 10 (assinatura + cartão/PIX com split + escrow)
fica live — **assumindo contrato Safe2Pay assinado** (TD-10-01..04). O back-office financeiro
(fatura/disputas-resolução/saques) **não** entra no deploy (Phase 15). **Fora de escopo:** features
novas de produto.
</domain>

<decisions>
## Implementation Decisions

### Jobs LGPD (REQ-048)
- **D-01:** Dois jobs arq aware-UTC idempotentes (padrão `lifecycle.py`): **anonimização** de PII de
  entidades inativas há **12 meses** (CPF/telefone/nome → hash/placeholder, preservando agregados
  estatísticos) e **exclusão** de rascunhos/dados efêmeros não-consumados há **30 dias**. Testados
  com **dados sintéticos** (nunca dados reais). Toda ação registrada (audit/contagem).
- **D-02:** Respeita retenções já existentes (locations 24h da Phase 9). Anonimização é irreversível
  e auditada; nunca apaga registros financeiros/fiscais exigidos por lei (estes seguem retenção legal).

### Infra LLM (REQ-053) — apenas infraestrutura
- **D-03:** Módulo `app/ai/` com **router** atrás de interface própria (Protocol), tabela
  `ai_usage_log` (global, ADR-001: provider, modelo, tokens, custo, latência, request_id, **sem PII**).
  Default usa **Claude** (modelo mais capaz — claude-opus-4-x para tarefas complexas; haiku p/ baratas)
  via adapter, com Stub em dev/test. **Nenhuma feature de IA ligada no M1** — só o trilho (router +
  log + config) para a v1.1 plugar sem refactor. Segue `domain/llm-integration-patterns`.

### Refino ETA / OSRM (REQ-054)
- **D-04:** Fallback de ETA robusto: OSRM primário → haversine/estimativa mediana (já existente da
  Phase 7/9) quando OSRM indisponível, com timeout e circuit breaker; nunca derruba criação de
  entrega. Métrica de qual caminho foi usado (observability).

### APK Capacitor (REQ-051)
- **D-05:** `capacitor.config.ts` já existe — completar config Android, gerar `android/` no CI,
  build de APK **debug** no pipeline (release assinado precisa de keystore → **checklist UAT humano**,
  não bloqueia o código). Exercitar câmera/GPS/push em device real = checklist humano (não automatizável).

### Validação de performance (REQ-050)
- **D-06:** Rodar o orçamento já configurado (`config.json performance_budget`, `lighthouserc.json`):
  LCP < 2500ms, INP < 200ms, CLS < 0.1, bundle main < 400KB gzip. p95 < 200ms em criar-entrega/
  aceitar-oferta sob carga sintética. Resultados viram relatório; violações viram TD com urgency_class.

### Release / deploy-safety
- **D-07:** Produzir **checklist de release** (secrets presentes, migrations aplicáveis, health checks,
  variáveis de ambiente, plists/keystore) via `gsd-release-auditor`. **Bloquear deploy** se houver
  BLOCKER. O cutover de produção do Safe2Pay (TD-10-01..04) é explicitamente sinalizado como
  dependente do **contrato assinado** (DEC-003/DEC-004) — o código está pronto atrás de Stub.
- **D-08:** O CI (`.github/workflows/ci.yml`) ganha os gates de release: test+lint+a11y(axe)+
  bundlesize+lighthouse verdes; build de APK debug. Segue `domain/github-actions-ci` +
  `domain/monorepo-deploy-safety`.

### Claude's Discretion
- Estratégia fina de anonimização por campo, escolha de modelo Claude por tarefa, layout do relatório
  de performance, organização do checklist de release.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Release / infra
- `.planning/ROADMAP.md` — Phase 14 (REQs 051/048/053/050/054; verificações; squad-audit pre-release)
- `.planning/DECISIONS.md` — ADR-001 (globais: ai_usage_log) · ADR-003 (APK Android M1) · DEC-003/004
  (Safe2Pay cutover dependente de contrato) · DRV-002 (UTC, retenção)
- `.planning/TECH-DEBT.md` — TD-10-01..04 (cutover Safe2Pay, pre_launch) · demais TDs pre_launch
- `specs/stack.yaml` · `apps/web/capacitor.config.ts` · `.github/workflows/ci.yml` · `tooling/ci/lighthouserc.json`
- `projeto/stacks/stack.md:53-60` · `projeto/docs-externos/integracoes.md:99-102`

### Padrões de código a reusar
- `apps/api/app/workers/lifecycle.py` — padrão de cron job aware-UTC idempotente (LGPD novos jobs)
- `app/integrations/base.py` — Protocol + Stub (modelo para o adapter LLM)
- `app/deliveries/service.py` / estimativa mediana (Phase 7) — base do fallback de ETA
- `app/core/config.py` — settings (config do LLM router, sem segredo em claro)

### Skills (Gate 4 + pre-release)
- `owasp-security` (auditoria completa) · `br/lgpd-compliance` · `quality/performance-web-vitals` ·
  `quality/accessibility-pro` · `quality/observability-production` · `domain/llm-integration-patterns` ·
  `domain/github-actions-ci` · `domain/monorepo-deploy-safety` · `webapp-testing` ·
  `mobile/offline-first` + `mobile/push-notifications-architecture` (validação no APK) ·
  `product/visual-regression-testing` · `ui-ux-pro-max` (web-design-audit)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lifecycle.py` já tem `purge_locations` (24h) — os jobs LGPD novos seguem o mesmo molde (cron, aware-UTC, idempotente, best-effort por linha, log de contagem).
- Padrão Protocol+Stub dos `integrations/` é o molde do adapter LLM (trocar provider sem doer — igual ao PSP atrás de interface).
- Estimativa mediana e geofence (Phases 7/9) já dão o fallback de ETA — o refino é robustez/observability, não algoritmo novo.
- `capacitor.config.ts`, `ci.yml`, `lighthouserc.json`, `performance_budget` no config — a infra de release já está parcialmente montada.

### Established Patterns
- Jobs em `WorkerSettings.cron_jobs`. Tabelas globais (ai_usage_log) sem area_id (ADR-001). PII fora de log.

### Integration Points
- Novos jobs registrados em `app/workers/settings.py`. Router LLM montado se/quando houver endpoint (M1: só infra). CI estendido em `.github/workflows/`.
</code_context>

<specifics>
## Specific Ideas
- "Infra de LLM sem feature": o trilho (router + log + config) pronto para a v1.1, mas **nada de IA
  ligado** no piloto — evita custo e risco sem bloquear o futuro.
- Deploy honesto: o checklist deixa explícito que o go-live de cartão/PIX depende do contrato Safe2Pay
  assinado (não esconder a dependência atrás do "código verde com Stub").

## Default de modelo (quando a v1.1 ligar IA)
- Usar os modelos Claude mais capazes (família claude-opus-4-x para raciocínio; haiku para tarefas
  baratas/alto volume) via adapter — decisão registrada para o router não nascer com modelo legado.
</specifics>

<deferred>
## Deferred Ideas
- Features de IA reais (ETA preditiva, antifraude por IA, copy assistida) — v1.1 (router já pronto).
- APK release assinado + publicação em loja — pós-piloto / M2 (iOS e lojas oficiais fora do M1).
- Back-office financeiro Safe2Pay — Phase 15 (pós-deploy).
</deferred>

---

*Phase: 14-hardening-apk-lgpd-e-release-piloto*
*Context gathered: 2026-06-11*
