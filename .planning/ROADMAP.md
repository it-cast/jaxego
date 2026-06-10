# ROADMAP — Jaxegô v1.0 (piloto Pádua)

> Gerado por `gsd-project-ingestor` em 2026-06-10. Interface contratual: autopilot e plan-checker leem flags e skills daqui — não inferem.
> 14 phases · 5 milestones · estimativa total ~20 semanas.
> Convenções: locale pt-BR; código/schema em inglês; tokens canônicos em `docs/identidade-visual/tokens.json`.
> **DEC-001 (2026-06-10):** dark mode é escopo do M1 → `ux-advanced/dark-mode-theming` é obrigatória em TODA phase com `has_ui: true` (3–14), além das listadas explicitamente.
> **DEC-002 (2026-06-10):** mapa de tracking em tempo real entra no M1 (ADR-101 promovida) → escopo detalhado na Phase 9.

---

## Phase 1: Fundação técnica (repo, infra, API skeleton)

**Milestone:** MS-01 · **Tipo:** foundation · **Status:** complete (2026-06-10) · **Estimativa:** M (3-5d)

### REQs cobertos
- REQ-052: Infra Docker Compose + CI/CD
- REQ-050 (base): observabilidade — Sentry, logs estruturados, request_id
- REQ-022 (fundação): migrations Alembic + convenções de schema

### Flags
- has_ui: false · has_api: true · mobile: false · integration_check: false
- has_ai: false · has_external_users: false · has_external_integration: false · has_payments: false · has_pii: false · is_pre_release: false

### Skills obrigatórias
- `meta/orchestration-decision-tree` · `quality/observability-production` · `domain/docker-production-ready` · `domain/mysql-schema-design` · `domain/github-actions-ci` · `domain/fastapi-production-patterns`

### Squad recomendado
- pre-phase: none · post-execute: none · pre-release: none

### Verificações automatizadas
- `docker compose up -d && curl -f localhost:8000/health` → exit 0
- `uv run pytest && uv run ruff check .` → exit 0
- Pipeline GitHub Actions verde no commit inicial

### Dependências
- Depende das phases: [] · Bloqueia: [2..14]

### Origem
- `projeto/stacks/stack.md:5-38` · `projeto/regras-negocio/regras.md:40-42` (convenções)

---

## Phase 2: Núcleo multi-área + autenticação + RBAC

**Milestone:** MS-01 · **Tipo:** foundation · **Status:** complete (2026-06-10) · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-001: multi-área `area_id` em tudo · REQ-002: entidade Área · REQ-004: append-only audit/transições · REQ-005: JWT+TOTP · REQ-006: anti-duplicidade · REQ-007: papéis e permissões

### Flags
- has_ui: false · has_api: true · mobile: false · integration_check: false
- has_ai: false · has_external_users: false · has_external_integration: false · has_payments: false · has_pii: true · is_pre_release: false

### Skills obrigatórias
- `meta/orchestration-decision-tree` · `quality/observability-production` · `owasp-security` (auth-and-session, api-input-validation) · `br/lgpd-compliance` · `domain/mysql-schema-design` · `domain/fastapi-production-patterns` · `product/api-design-contracts`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Teste de isolamento: seed 2 áreas, query cross-área → 403 (exit 0 na suíte)
- Teste de trigger: UPDATE em `audit_log` → erro MySQL
- Teste de lockout: 6ª tentativa de login em 15 min → 423/429

### Dependências
- Depende das phases: [1] · Bloqueia: [3..14]

### Origem
- `projeto/decisoes-existentes/adrs.md:7-11` (ADR-001), `:28-31` (ADR-005) · `projeto/regras-negocio/regras.md` RN-001/011/012 · `projeto/regras-negocio/visao-geral.md:25-34`

---

## Phase 3: Shell frontend + design system (3 superfícies)

**Milestone:** MS-01 · **Tipo:** ui · **Status:** not_started · **Estimativa:** M (3-5d)

### REQs cobertos
- REQ-056: tokens/voz/vocabulário (claro + escuro — DEC-001) · REQ-055 (fundação): componentes de estado (empty/error/loading/warn) · REQ-005 (UI): tela 01-login

### Flags
- has_ui: true · has_api: true · mobile: true (shell Ionic) · integration_check: false · dark_mode: true (DEC-001)
- has_ai: false · has_external_users: true · has_external_integration: false · has_payments: false · has_pii: false · is_pre_release: false

### Skills obrigatórias
- `meta/orchestration-decision-tree` · `quality/observability-production` · `ui-ux-pro-max` · `quality/accessibility-pro` · `product/component-library-governance` · `ux-advanced/design-tokens-system` · `ux-advanced/dark-mode-theming` (DEC-001 — tokens dark + alternância de tema) · `ux-advanced/empty-states-polish` · `br/ux-copywriting-ptbr` · `quality/error-ux-patterns` · `ux-advanced/responsive-breakpoint-strategy` · `domain/angular-material-patterns` · `domain/ionic-patterns`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- `grep -r "#E84E1B\|#FAF6EE" src/ --include="*.scss" | grep -v tokens` → 0 ocorrências (nada de cor hardcoded fora da geração de tokens)
- Build Angular com lazy por rota; axe sem violações críticas na tela de login
- Alternância de tema claro↔escuro funcional (DEC-001); contraste AA nos dois temas; tokens dark presentes em `tokens.json`/CSS vars

### Dependências
- Depende das phases: [2] · Bloqueia: [4..14 com UI]

### Origem
- `projeto/identidade-visual/tokens.json` (canônico) · `projeto/identidade-visual/brand.md` · `projeto/wireframes/01-login.html` · ADR-003 (`adrs.md:18-21`)

---

## Phase 4: Cadastro e ativação de loja

**Milestone:** MS-02 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-008: F-01 completo com 4 exceções · REQ-009: seeds de planos `[ASSUMIDO]` · REQ-006 (aplicado)

### Flags
- has_ui: true · has_api: true · mobile: false · integration_check: true (Receita Federal, SMS, SES)
- has_ai: false · has_external_users: true · has_external_integration: true · has_payments: false · has_pii: true · is_pre_release: false

### Skills obrigatórias
- `meta/orchestration-decision-tree` · `quality/observability-production` · matriz UI completa (ui-ux-pro-max, accessibility-pro, component-library-governance, design-tokens-system, empty-states-polish) · `br/ux-copywriting-ptbr` · `br/brazilian-forms` (CNPJ/CPF/telefone) · `ux-advanced/form-ux-mastery` · `quality/error-ux-patterns` · `ux-advanced/onboarding-patterns` · `owasp-security/api-input-validation` · `br/lgpd-compliance`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Testes das exceções F-01 E1–E4 (CNPJ inativo, colisão, pagamento falha→Free, Receita fora→pending_validation+retry)
- Wireframe-contract de `02-cadastro-loja.html` coberto no UI-SPEC

### Dependências
- Depende das phases: [3] · Bloqueia: [6, 7]

### Origem
- `projeto/regras-negocio/fluxos.md:7-24` (F-01) · `projeto/wireframes/02-cadastro-loja.html` · `projeto/docs-externos/integracoes.md:55-59`

---

## Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2

**Milestone:** MS-02 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-013: wizard F-02 · REQ-014: validação simples/completa item a item · REQ-015: documentos B2 privado · REQ-019 (parcial): flag `mei_pending`

### Flags
- has_ui: true · has_api: true · mobile: true · integration_check: true (B2, Receita p/ MEI, SMS)
- has_ai: false · has_external_users: true · has_external_integration: true · has_payments: false · has_pii: true · is_pre_release: false

### Skills obrigatórias
- matriz UI completa + `br/ux-copywriting-ptbr` · `br/brazilian-forms` · `ux-advanced/form-ux-mastery` · `quality/error-ux-patterns` · `ux-advanced/file-upload-ux` (selfie/CNH/CRLV) · `ux-advanced/onboarding-patterns` · `ux-advanced/trust-safety-ux` · `ux-advanced/gesture-touch-patterns` (mobile) · `owasp-security` (upload, data-protection) · `br/lgpd-compliance` · `quality/observability-production`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Bucket KYC inacessível sem URL assinada (teste de integração)
- Testes F-02 E1–E5 (retomada 30d, CPF outra área, MEI pendente, reenvio de item, escalação 48h)
- Wireframe-contract de `03-cadastro-entregador.html` e `19-admin-area-entregador-detalhe.html`

### Dependências
- Depende das phases: [3] · Bloqueia: [6, 8]

### Origem
- `projeto/regras-negocio/fluxos.md:27-48` (F-02) · ADR-011 (`adrs.md:60-64`) · ADR-004 · `projeto/docs-externos/integracoes.md:85-88`

---

## Phase 6: Área operável — bairros, config, cobertura e tabela de frete

**Milestone:** MS-02 · **Tipo:** core · **Status:** not_started · **Estimativa:** M (3-5d)

### REQs cobertos
- REQ-003: catálogo de bairros · REQ-002 (UI config — tela 21) · REQ-016: cobertura coleta E entrega · REQ-017: tabela de frete com piso · REQ-018: online/offline/busy · REQ-044 (parcial): KYC fila + config + bairros

### Flags
- has_ui: true · has_api: true · mobile: true (telas do entregador) · integration_check: false
- has_ai: false · has_external_users: true · has_external_integration: false · has_payments: false · has_pii: false · is_pre_release: false

### Skills obrigatórias
- matriz UI completa + `br/ux-copywriting-ptbr` · `ux-advanced/form-ux-mastery` · `quality/error-ux-patterns` · `ux-advanced/saas-dashboard-patterns` (admin) · `ux-advanced/data-tables-ux` · `domain/mysql-schema-design` (spatial: POINT/POLYGON)

### Squad recomendado
- pre-phase: none · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Teste espacial: ponto dentro/fora de polígono de bairro decide elegibilidade
- Preço abaixo do piso → rejeição com mensagem citando piso (RN-015)
- Wireframe-contract de `10`, `17`, `18`, `21`

### Dependências
- Depende das phases: [4, 5] · Bloqueia: [7, 8]

### Origem
- ADR-006 (`adrs.md:33-36`) · RN-003/015 · `projeto/wireframes/10,17,18,21` · `projeto/regras-negocio/fluxos.md:156-171` (F-08)

---

## Phase 7: Criação de entrega + máquina de estados (modalidade direta)

**Milestone:** MS-03 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-021: F-03 (pagamento direto primeiro; cartão/PIX na Phase 10) · REQ-022: 7 estados append-only · REQ-023: estimativa de frete `[ASSUMIDO RN-030]` · REQ-011 (parcial): limite do plano

### Flags
- has_ui: true · has_api: true · mobile: false · integration_check: false
- has_ai: false · has_external_users: true · has_external_integration: false · has_payments: false · has_pii: true · is_pre_release: false

### Skills obrigatórias
- matriz UI completa + `br/ux-copywriting-ptbr` · `ux-advanced/form-ux-mastery` · `quality/error-ux-patterns` · `br/brazilian-forms` · `product/api-design-contracts` · `owasp-security/api-input-validation` · `quality/observability-production` (métrica criação)

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Teste exaustivo de transições inválidas da máquina de estados (RN-019)
- Testes F-03 E1/E2/E4 (E3 pagamento e E5 fatura entram nas phases 10–11 com guarda já prevista)
- Wireframe-contract de `12-loja-nova-entrega.html`, `11-loja-dashboard.html`, `14-loja-entregas.html`

### Dependências
- Depende das phases: [6] · Bloqueia: [8]

### Origem
- `projeto/regras-negocio/fluxos.md:51-69` (F-03) · RN-019/023/028/030 · `projeto/wireframes/11,12,14`

---

## Phase 8: Despacho em cascata + oferta + aceite

**Milestone:** MS-03 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-024: cascata favoritos→auto com locks · REQ-025: privacidade do destino (RN-013) · REQ-012 (dados): favoritos/bloqueados na elegibilidade · REQ-054: OSRM/ETA `[ASSUMIDO]`

### Flags
- has_ui: true · has_api: true · mobile: true (app do entregador) · integration_check: true (OSRM, push)
- has_ai: false · has_external_users: true · has_external_integration: true · has_payments: false · has_pii: false · is_pre_release: false

### Skills obrigatórias
- matriz UI completa + `br/ux-copywriting-ptbr` · `ux-advanced/gesture-touch-patterns` · `product/micro-animations-delight` + `ux-advanced/motion-design-patterns` (cronômetro/sheet de oferta — motion não-trivial) · `mobile/push-notifications-architecture` · `quality/observability-production` (KPI tempo até aceite) · `systematic-debugging` (concorrência)

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Teste de corrida: 2 aceites simultâneos → lock garante 1 vencedor (F-05 E3)
- Teste de contrato: payload de oferta sem endereço completo do destino (RN-013)
- Redis TTL como fonte de verdade do timer (ADR-104); timeout → próximo da cascata
- Wireframe-contract de `05-entregador-oferta.html`, `04-entregador-home.html`

### Dependências
- Depende das phases: [7] · Bloqueia: [9]

### Origem
- ADR-007 (`adrs.md:38-41`) · ADR-104 · `projeto/regras-negocio/fluxos.md:90-106` (F-05) · `projeto/wireframes/04,05`

---

## Phase 9: Execução, comprovação, tracking público e notificações

**Milestone:** MS-03 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-026: F-06 com 6 exceções · REQ-027: foto+EXIF/GPS geofence · REQ-028: número de referência · REQ-029: cancelamentos RN-004 · REQ-030: tracking público **com mapa em tempo real (DEC-002 — promove ADR-101 ao M1)** · REQ-031: notificações 3 momentos · REQ-032: janela de telefones · REQ-035 (parcial): confirmação de pagamento direto na comprovação · REQ-049: multicanal com fallback · REQ-055: estados de UI

### Flags
- has_ui: true · has_api: true · mobile: true · integration_check: true (B2, SMS, SES, push, tiles OSM)
- has_ai: false · has_external_users: true · has_external_integration: true · has_payments: false · has_pii: true · is_pre_release: false

### Escopo de tracking ao vivo (DEC-002 / ADR-101 promovida)
- App do entregador faz polling de localização (HTTP 60–120s, filtro de movimento 50m, Page Visibility API pausa quando em background)
- Tabela `delivery_locations` (retenção 24h pós-entrega); endpoint de ingestão de posição autenticado por entrega na janela ACEITA→FINALIZADA
- Tracking público (tela 26) renderiza mapa com tiles OpenStreetMap/MapLibre + posição aproximada do entregador; nunca expõe PII do entregador além do permitido (RN-013/RN-022)

### Skills obrigatórias
- matriz UI completa + `br/ux-copywriting-ptbr` · `ux-advanced/gesture-touch-patterns` · `mobile/offline-first` (upload offline-tolerante + polling resiliente) · `mobile/push-notifications-architecture` · `ux-advanced/file-upload-ux` (câmera) · `quality/error-ux-patterns` · `ux-advanced/trust-safety-ux` (tracking público) · `owasp-security` (link público, EXIF server-side, endpoint de localização) · `br/lgpd-compliance` (RN-022, PII no tracking + retenção de localização) · `quality/performance-web-vitals` (mapa não pode degradar LCP) · `quality/observability-production`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Foto sem GPS/fora do raio → rejeição server-side com motivo; 3 falhas → `low_confidence`
- Telefone inacessível fora de ACEITA→FINALIZADA (teste por estado)
- Tracking público responde sem auth; link inválido → estado de erro
- Job FINALIZADA 24h pós-ENTREGUE sem disputa
- Localização ao vivo (DEC-002): posição só aceita na janela ACEITA→FINALIZADA; `delivery_locations` expira em 24h; polling pausa com aba em background; mapa público não vaza PII do entregador
- Wireframe-contract de `06`, `07`, `13`, `26`

### Dependências
- Depende das phases: [8] · Bloqueia: [10, 11]

### Origem
- `projeto/regras-negocio/fluxos.md:109-128` (F-06) · RN-004/005/013/017/018/022/026 · ADR-008 · `projeto/wireframes/06,07,13,26` · `projeto/docs-externos/integracoes.md:63-95`

---

## Phase 10: Safe2Pay núcleo — assinaturas, cobrança com split, escrow, estornos

**Milestone:** MS-04 · **Tipo:** integration · **Status:** not_started · **Estimativa:** L (1-2sem)
**⚠ BLOQUEADA por OQ-3 até validação do contrato Safe2Pay (split, prazo de repasse, taxas).**

### REQs cobertos
- REQ-010: assinatura recorrente · REQ-011: upgrade pro-rata/downgrade `[ASSUMIDO RN-029]` · REQ-034: cobrança por entrega com split · REQ-036: escrow 24h · REQ-029 (financeiro): estornos · REQ-019 (completo): subconta do entregador

### Flags
- has_ui: true · has_api: true · mobile: false · integration_check: true (Safe2Pay end-to-end)
- has_ai: false · has_external_users: true · has_external_integration: true · has_payments: true · has_pii: true · is_pre_release: false

### Skills obrigatórias
- `domain/safe2pay-escrow-br` (546 linhas — obrigatória) · `domain/saas-billing-canonical` + `docs/SAAS-BILLING-DOCS.md` (CLAUDE.md §18 — lei) · `ux-advanced/payment-checkout-ux` + `ux-advanced/trust-safety-ux` · `owasp-security` (auth-and-session, idempotência, webhooks) · `quality/observability-production` (conciliação, alertas) · matriz UI (telas de checkout/plano) · `br/ux-copywriting-ptbr`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Recusa de cartão → entrega NÃO criada (teste F-03 E3)
- Split corrida/taxa/revenue-share com soma exata; idempotência por `Reference`
- Webhook Safe2Pay duplicado → processado uma vez (`IdTransaction`)
- Circuit breaker: API fora → criação cartão/PIX indisponível, direto segue

### Dependências
- Depende das phases: [9] · Bloqueia: [11, 12]

### Origem
- ADR-009 v2 (`adrs.md:48-53`) · `projeto/docs-externos/integracoes.md:7-36` · `projeto/regras-negocio/fluxos.md:134-152` (F-07) · RN-006/010/029

---

## Phase 11: Pagamento direto completo — fatura, disputas, saques

**Milestone:** MS-04 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-035 (completo): pagamento direto 1ª classe · REQ-037: fatura mensal `[ASSUMIDO RN-025]` · REQ-038: saques `[ASSUMIDO R$ 20]` · REQ-039: disputas + RN-027 `[ASSUMIDO]` · REQ-040: conciliação diária · REQ-012 (UI tela 15)

### Flags
- has_ui: true · has_api: true · mobile: true (extrato/saque do entregador) · integration_check: true (Safe2Pay boleto/PIX/transferência)
- has_ai: false · has_external_users: true · has_external_integration: true · has_payments: true · has_pii: true · is_pre_release: false

### Skills obrigatórias
- `domain/safe2pay-escrow-br` · `domain/saas-billing-canonical` + SAAS-BILLING-DOCS.md · `ux-advanced/payment-checkout-ux` · `ux-advanced/trust-safety-ux` (disputas) · `ux-advanced/data-tables-ux` (faturas/extrato) · matriz UI + `br/ux-copywriting-ptbr` · `owasp-security` · `quality/observability-production`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Job fecha fatura dia 1º; vencida >7 dias → criação de entrega bloqueada (F-03 E5)
- "Não recebi" → ENTREGUE + disputa; 2 procedentes/30d → modalidade direta bloqueada 90 dias
- Saque falha → saldo restituído; saque < R$ 20 → rejeitado
- Wireframe-contract de `08`, `15`, `16`

### Dependências
- Depende das phases: [10] · Bloqueia: [13]

### Origem
- ADR-012 (`adrs.md:66-71`) · RN-025/026/027 · `projeto/wireframes/08,15,16` · `projeto/regras-negocio/fluxos.md:142-152`

---

## Phase 12: API pública + integração Menu Certo

**Milestone:** MS-04 · **Tipo:** integration · **Status:** not_started · **Estimativa:** M (3-5d)

### REQs cobertos
- REQ-041: `POST /v1/deliveries` idempotente · REQ-042: API keys (RN-020) · REQ-043: webhooks HMAC com retry

### Flags
- has_ui: true (tela 22 API keys) · has_api: true · mobile: false · integration_check: true (round-trip Menu Certo simulado)
- has_ai: false · has_external_users: false · has_external_integration: true · has_payments: false · has_pii: true · is_pre_release: false

### Skills obrigatórias
- `product/api-design-contracts` · `owasp-security` (api-input-validation, HMAC, anti-replay) · `quality/observability-production` (health de webhook, rate limit) · `domain/fastapi-production-patterns` · matriz UI mínima (tela 22) + `ux-advanced/data-tables-ux`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- Idempotency-Key repetida → mesma resposta (F-04 E1); 429 com Retry-After (E4); 401 estável (E2)
- Receptor fake valida `X-Jaxego-Signature` e janela de 5 min; retry exato 0s/30s/2min/10min/1h/4h/12h/24h
- Revogação de chave efetiva em <1 min
- Wireframe-contract de `22-admin-area-apikeys.html`

### Dependências
- Depende das phases: [10] · Bloqueia: [14]

### Origem
- ADR-010 (`adrs.md:55-58`) · `projeto/regras-negocio/fluxos.md:72-86` (F-04) · `projeto/docs-externos/integracoes.md:40-51` · RN-020

---

## Phase 13: Governança — admin plataforma, score, avaliações, suspensão/recurso

**Milestone:** MS-05 · **Tipo:** core · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-046: admin plataforma (telas 23–25) · REQ-020: score explicável · REQ-033: avaliações · REQ-045: suspensão/recurso com reversão automática · REQ-047: revenue share `[DECIDIR %]` · REQ-044 (completo): disputas/suspensões na UI do admin de área

### Flags
- has_ui: true · has_api: true · mobile: false · integration_check: false
- has_ai: false · has_external_users: true · has_external_integration: false · has_payments: false · has_pii: true · is_pre_release: false

### Skills obrigatórias
- matriz UI + `br/ux-copywriting-ptbr` · `ux-advanced/saas-dashboard-patterns` · `ux-advanced/data-tables-ux` · `ux-advanced/search-filter-ux` (listas admin) · `ux-advanced/trust-safety-ux` (suspensão com recurso) · `owasp-security` (MFA, escopo cross-área auditado) · `quality/observability-production`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · pre-release: none

### Verificações automatizadas
- SLA de recurso estourado → suspensão revertida + alerta (job testado)
- Snapshot diário de score com componentes/pesos; nenhum efeito financeiro ligado a score
- Admin plataforma sem TOTP → bloqueado
- Wireframe-contract de `09`, `19`, `20`, `23`, `24`, `25`

### Dependências
- Depende das phases: [11] · Bloqueia: [14]

### Origem
- ADR-013 (`adrs.md:73-76`) · RN-008/014/016 · `projeto/wireframes/09,19,20,23,24,25` · `projeto/regras-negocio/visao-geral.md:29`

---

## Phase 14: Hardening, APK, LGPD e release piloto

**Milestone:** MS-05 · **Tipo:** release · **Status:** not_started · **Estimativa:** L (1-2sem)

### REQs cobertos
- REQ-051: APK Capacitor `[ASSUMIDO]` · REQ-048: jobs LGPD · REQ-053: infra LLM (router + ai_usage_log) · REQ-050 (completo): p95/LCP validados · REQ-054 (refino): fallbacks de ETA

### Flags
- has_ui: true · has_api: true · mobile: true · integration_check: true (smoke end-to-end de todas as integrações)
- has_ai: true (infra apenas) · has_external_users: true · has_external_integration: true · has_payments: true (regressão) · has_pii: true · **is_pre_release: true**

### Skills obrigatórias
- `quality/performance-web-vitals` · `quality/accessibility-pro` (auditoria) · `quality/observability-production` · `br/lgpd-compliance` · `owasp-security` (auditoria completa) · `webapp-testing` · `mobile/offline-first` + `mobile/push-notifications-architecture` (validação no APK real) · `product/visual-regression-testing` · `product/ai-integration-patterns`/`domain/llm-integration-patterns` (router) · web-design-audit equivalente via `ui-ux-pro-max`

### Squad recomendado
- pre-phase: squad-research · post-execute: squad-review · **pre-release: squad-audit**

### Verificações automatizadas
- APK gerado no CI, instala e exerce câmera/GPS/push em device real (checklist UAT humano)
- Job de anonimização 12 meses + exclusão 30 dias testados com dados sintéticos
- p95 < 200 ms em criar-entrega/aceitar-oferta sob carga sintética; LCP < 2.500 ms 4G
- Suíte completa + lint verdes; zero FAIL-BLOCK do Senior Quality Bar

### Dependências
- Depende das phases: [12, 13] · Bloqueia: []

### Origem
- ADR-003 · RN-021 · `projeto/stacks/stack.md:53-60` · `projeto/docs-externos/integracoes.md:99-102`

---

## Visão geral

| Phase | Nome | MS | ui | mobile | has_api | integration_check | payments | Estimativa |
|---|---|---|---|---|---|---|---|---|
| 1 | Fundação técnica | 01 | – | – | ✓ | – | – | M |
| 2 | Multi-área + auth | 01 | – | – | ✓ | – | – | L |
| 3 | Shell + design system | 01 | ✓ | ✓ | ✓ | – | – | M |
| 4 | Cadastro loja | 02 | ✓ | – | ✓ | ✓ | – | L |
| 5 | Cadastro entregador/KYC | 02 | ✓ | ✓ | ✓ | ✓ | – | L |
| 6 | Área operável | 02 | ✓ | ✓ | ✓ | – | – | M |
| 7 | Criação de entrega | 03 | ✓ | – | ✓ | – | – | L |
| 8 | Despacho em cascata | 03 | ✓ | ✓ | ✓ | ✓ | – | L |
| 9 | Execução + tracking | 03 | ✓ | ✓ | ✓ | ✓ | – | L |
| 10 | Safe2Pay núcleo ⚠OQ-3 | 04 | ✓ | – | ✓ | ✓ | ✓ | L |
| 11 | Direto + fatura + saques | 04 | ✓ | ✓ | ✓ | ✓ | ✓ | L |
| 12 | API pública/Menu Certo | 04 | ✓ | – | ✓ | ✓ | – | M |
| 13 | Governança + score | 05 | ✓ | – | ✓ | – | – | L |
| 14 | Hardening + release | 05 | ✓ | ✓ | ✓ | ✓ | ✓ | L |
