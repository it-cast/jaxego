# Skills Index — v0.9.5

> Catálogo completo de skills disponíveis no framework. Consumido pelo `gsd-planner` e pelo `gsd-plan-checker` para enforcement.
> Formato de cada skill: `.claude/skills/<categoria>/<nome>/SKILL.md` (algumas têm `data/` + `scripts/`).

## Legenda

- ⭐ **Expandida** — conteúdo completo, pronto para uso
- 🔒 **Obrigatória** (quando aplicável) — plan-checker bloqueia plano que não cite
- 🇧🇷 **pt-BR específica** — aplicável apenas a projetos com locale pt-BR
- 📦 **Tem data/scripts** — pasta contém recursos além do SKILL.md

**Total: 73 skills em 9 categorias** (67 → 72 com v0.9.5: +fastapi-production-patterns, +github-actions-ci, +data-tables-ux, +search-filter-ux, +parallel-orchestration)

> ⚠️ **Fonte de verdade da contagem:** este índice é curado manualmente e pode defasar. A contagem real e os triggers efetivos vêm de `find .claude/skills -name SKILL.md` (arquivos) + `find .claude/skills -name triggers.yaml` (enforcement). O plan-checker (gate 3) lê os `triggers.yaml`, não esta tabela.

### Novas obrigatórias por contexto (v0.9.5)

| Skill | 🔒 quando |
|-------|-----------|
| `domain/fastapi-production-patterns` | `has_api: true` ou phase cria/altera endpoint |
| `ux-advanced/data-tables-ux` | `has_admin: true` ou phase com tabela/listagem |
| `ux-advanced/search-filter-ux` | phase com busca/filtro/período |
| `domain/github-actions-ci` | phase toca `.github/workflows/**` |
| `meta/parallel-orchestration` | `parallelization.task_level: true` |
| `quality/senior-quality-bar` | toda phase com código (Gate 8) |


---

## br/ — Brasil-específico (3 skills) 🇧🇷

| Skill | Estado | Obrigatória para |
|-------|--------|-------------------|
| ⭐ `br/brazilian-forms` | expandida | Qualquer form com CPF/CNPJ/CEP/phone (🔒) |
| ⭐ `br/ux-copywriting-ptbr` | expandida | UI em pt-BR (🔒) |
| ⭐ `br/lgpd-compliance` | expandida | Manipulação de PII (🔒) |

---

## domain/ — Stacks e padrões específicos (10 skills)

| Skill | Estado | Uso típico |
|-------|--------|------------|
| ⭐ `domain/angular-material-patterns` | expandida | Projetos Angular + Material |
| ⭐ `domain/docker-production-ready` | expandida | Dockerfiles prontos para produção |
| ⭐ `domain/ionic-patterns` | expandida | Apps Ionic/Capacitor |
| ⭐ `domain/llm-integration-patterns` | expandida (869 linhas) | Integração com LLMs (OpenAI, Anthropic, etc.) |
| ⭐ `domain/mysql-schema-design` | expandida | Design de schema MySQL |
| ⭐ `domain/{gateway-pagamento}-escrow-br` | expandida (546 linhas) | 🇧🇷 Integração com {gateway-pagamento} escrow |
| 🆕 `domain/monorepo-deploy-safety` | nova v0.9.3 | Symlink atomic deploy, ordem migrations, invariantes Phase 1, quando usar Nx (não Turborepo) |
| 🆕 `domain/saas-billing-canonical` | nova v0.9.x | 🔒 Billing/subscription/payment/checkout — padrão canônico |
| 🆕 `domain/fastapi-production-patterns` | nova v0.9.5 | 🔒 Backend FastAPI (has_api): estrutura, Pydantic v2, auth, erros, jobs, testes |
| 🆕 `domain/github-actions-ci` | nova v0.9.5 | CI/CD: pipeline canônico, GHCR, deploy VPS, build mobile, secrets |

---

## meta/ — Workflows de processo e decisão (16 skills)

| Skill | Estado | Uso típico |
|-------|--------|------------|
| ⭐ `meta/design-to-code` | expandida (271 linhas) | Ponte design system ↔ implementação |
| ⭐ `meta/orchestration-decision-tree` | expandida | Consumida pelo `gsd-orchestrator` para rotear intent |
| ⭐ `meta/project-kickoff-interview` | expandida | Primeira sessão em projeto novo |
| ⭐ `meta/stack-advisor` | expandida | Aconselhamento de stack técnica |
| 🆕 `meta/composition-patterns` | nova v0.8.1 | Refactor de boolean prop proliferation, compound components, design de API de componente |
| 🆕 `meta/parallel-orchestration` | nova v0.9.5 | Particionamento seguro de tasks paralelas — base do gsd-wave-dispatcher |
| ⭐ `meta/competitive-analysis` | expandida | Análise de concorrentes |
| ⭐ `meta/empathy-map` / `journey-map` / `jobs-to-be-done` / `user-persona` | expandidas | Discovery de produto |
| ⭐ `meta/north-star-vision` / `opportunity-framework` / `productivity-estimation` / `refactoring-ui` | expandidas | Visão, priorização, estimativa, polish |

---

## mobile/ — Mobile específico (2 skills)

| Skill | Estado | Obrigatória para |
|-------|--------|-------------------|
| ⭐ `mobile/offline-first` | expandida (450 linhas) | Apps mobile com rede (🔒) |
| ⭐ `mobile/push-notifications-architecture` | expandida | Fases com push notification |

---

## product/ — API, design system, componentes (4 skills)

| Skill | Estado | Obrigatória para |
|-------|--------|-------------------|
| ⭐ `product/api-design-contracts` | expandida (374 linhas) | Novo endpoint (🔒) |
| ⭐ `product/visual-regression-testing` | expandida | Componentes de design system |
| ⭐ `product/component-library-governance` | expandida | Mudanças em design system |
| ⭐ `product/micro-animations-delight` | expandida (398 linhas) | Fases com UI avançada |

---

## quality/ — Cross-cutting (6 skills)

| Skill | Estado | Obrigatória para |
|-------|--------|-------------------|
| ⭐ `quality/performance-web-vitals` | expandida | Fases com UI ou endpoint em prod (🔒) |
| ⭐ `quality/error-ux-patterns` | expandida | Fases com UI ou error handling (🔒) |
| ⭐ `quality/observability-production` | expandida (351 linhas) | Qualquer endpoint, job, integração (🔒) |
| ⭐ `quality/accessibility-pro` | expandida | Fases com UI (🔒) |
| ⭐ `quality/i18n-ready-architecture` | expandida | Projetos multi-locale |
| 🆕 `quality/web-design-audit` | nova v0.8.1 | Phase-close com UI: auditoria sistemática contra 100+ regras Web Interface Guidelines |

---

## ux-advanced/ — Padrões profundos de UX (20 skills)

Estas skills cobrem padrões de UX não endereçados pelas `quality/` e `product/`. Extraídas do GSD base e integradas ao framework.

| Skill | Estado | Quando obrigatória |
|-------|--------|---------------------|
| ⭐ `ux-advanced/chat-ux-patterns` | expandida | Features com chat/conversa |
| ⭐ `ux-advanced/dark-mode-theming` | expandida | Projetos que suportam tema escuro |
| ⭐ `ux-advanced/design-tokens-system` | expandida (357 linhas) | Projetos com tokens.json (🔒 para UI) |
| ⭐ `ux-advanced/empty-states-polish` | expandida (362 linhas) | Telas com listagens ou estados vazios (🔒) |
| ⭐ `ux-advanced/file-upload-ux` | expandida (369 linhas) | Features com upload de arquivo |
| ⭐ `ux-advanced/form-ux-mastery` | expandida (266 linhas) | Formulários (🔒 quando has_forms=true) |
| ⭐ `ux-advanced/gesture-touch-patterns` | expandida | Apps mobile (🔒 no mobile) |
| ⭐ `ux-advanced/motion-design-patterns` | expandida (365 linhas) | UI com animação (complementa micro-animations-delight) |
| ⭐ `ux-advanced/onboarding-patterns` | expandida (294 linhas) | Fluxos de onboarding (🔒 em fases de auth/signup) |
| ⭐ `ux-advanced/payment-checkout-ux` | expandida | Fluxos de pagamento (🔒 em fases de checkout) |
| ⭐ `ux-advanced/responsive-breakpoint-strategy` | expandida (322 linhas) | Projetos web responsivos (🔒 para UI web) |
| ⭐ `ux-advanced/saas-dashboard-patterns` | expandida (464 linhas) | Dashboards SaaS/admin |
| ⭐ `ux-advanced/trust-safety-ux` | expandida | Fluxos sensíveis (pagamento, dados pessoais, exclusão) |
| ⭐ `ux-advanced/ui-input-rich-patterns` | expandida (741 linhas) | Inputs avançados (date picker, search, combobox, etc.) |
| 🆕 `ux-advanced/data-tables-ux` | nova v0.9.5 | Tabelas de dados — 🔒 em painel admin/B2B (paginação, bulk, mobile, vazios) |
| 🆕 `ux-advanced/search-filter-ux` | nova v0.9.5 | Busca + filtros — chips ativos, estado na URL, FULLTEXT, zero-results |
| ⭐ `ux-advanced/data-visualization` / `feedback-patterns` / `loading-states` | expandidas | Gráficos, feedback, loading |

---

## Standalone — skills transversais (6 skills)

| Skill | Estado | Uso típico |
|-------|--------|------------|
| ⭐ `owasp-security` | expandida | Security patterns; invocada por `security-auditor` e `gsd-security-auditor` |
| ⭐ `prompt-engineering` | expandida | Guidelines para invocar LLMs com prompts eficientes |
| ⭐ `spartan-ai-toolkit` | expandida | Toolkit de orquestração com múltiplos agentes LLM |
| ⭐ `systematic-debugging` | expandida | Metodologia de debug — consumida por `gsd-debugger` |
| ⭐ `ui-ux-pro-max` v2.1 📦 | upgraded em v0.8.1 (658 linhas + 1.7MB data + 88KB scripts) | Design intelligence v2.1 com Reasoning Rules — 84 styles, 161 paletas, 161 product types, 73 font pairings, 99 UX guidelines, 16 stacks (+Angular, Astro, Laravel, Three.js, Jetpack Compose). Design system generator + persistência (`design-system/MASTER.md` + page overrides). 🔒 para UI |
| ⭐ `webapp-testing` 📦 | expandida | Testes end-to-end com Playwright |

---

## Matriz canônica: `sprint_ui_matrix` v0.3

Esta matriz é consumida pelo plan-checker ao validar `SPRINT.md` com `has_ui: true`.

### Sempre obrigatórias (se `has_ui: true`)
- 🔒 `product/component-library-governance`
- 🔒 `quality/accessibility-pro`
- 🔒 `ux-advanced/design-tokens-system`
- 🔒 `ui-ux-pro-max` (direção estética — evita "AI slop")
- 🔒 `ux-advanced/empty-states-polish`

### Obrigatórias por locale
- Se `locale: pt-BR` → 🔒 `br/ux-copywriting-ptbr`

### Obrigatórias por flag
- Se `has_forms: true` → 🔒 `ux-advanced/form-ux-mastery` + 🔒 `quality/error-ux-patterns`
- Se `has_error_states: true` → 🔒 `quality/error-ux-patterns`
- Se `has_non_trivial_motion: true` → 🔒 `product/micro-animations-delight` + 🔒 `ux-advanced/motion-design-patterns`
- Se `touches_shared_components: true` → 🔒 `product/visual-regression-testing`

### Obrigatórias por contexto do projeto
- Se projeto é mobile (`has_mobile: true`) → 🔒 `ux-advanced/gesture-touch-patterns`
- Se projeto é web responsivo → 🔒 `ux-advanced/responsive-breakpoint-strategy`
- Se projeto suporta dark mode → 🔒 `ux-advanced/dark-mode-theming`

### Obrigatórias por feature
- Feature de onboarding/signup → 🔒 `ux-advanced/onboarding-patterns` + 🔒 `ux-advanced/trust-safety-ux`
- Feature de pagamento/checkout → 🔒 `ux-advanced/payment-checkout-ux` + 🔒 `ux-advanced/trust-safety-ux`
- Feature de upload de arquivo → 🔒 `ux-advanced/file-upload-ux`
- Feature de chat/mensagem → 🔒 `ux-advanced/chat-ux-patterns`
- Dashboard SaaS/admin → 🔒 `ux-advanced/saas-dashboard-patterns`

---

## Como o enforcement funciona

1. **Plan-checker** carrega todas as skills indexadas aqui
2. Para cada `SPRINT.md`/`PLAN.md`, roda matriz contra flags do front-matter
3. Skills marcadas 🔒 (obrigatórias quando aplicáveis) precisam aparecer em `## Skills Consultadas` ou `## Skills Dispensadas (com justificativa)`
4. **Ausência de qualquer skill obrigatória = BLOCK** (v0.3 endurece — antes era 2+)

Ver `.claude/get-shit-done/references/skills-enforcement.md` para detalhes.

---

## Notas de versão

- **v0.8.1 (2026-05-09):** 2 skills novas + 1 upgrade major:
  - 🆕 `meta/composition-patterns` — adaptado de [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) (MIT). Resolve boolean prop proliferation via compound components, state lifting, explicit variants. Tier 2.
  - 🆕 `quality/web-design-audit` — adaptado de [vercel-labs/agent-skills/web-design-guidelines](https://github.com/vercel-labs/agent-skills) (MIT, 133k installs/sem). Auditoria contra 100+ regras Web Interface Guidelines. Tier 2.
  - ⬆️ `ui-ux-pro-max` v1 → **v2.1** ([nextlevelbuilder MIT](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), 29.6k stars). Reasoning Rules (engine BM25 + JSON conditions), design system generator com persistência, 84/161/161 (styles/palettes/products), +3 stacks (Angular, Astro, Laravel, Three.js, Jetpack Compose). Security check passou: zero `urllib`/`requests`/`subprocess`/`exec`/`eval` nos scripts; zero prompt injection na SKILL.md.
  - Total: 44 → 46 skills.
- **v0.3.0 (2026-04-22):** 30 skills novas adicionadas do GSD base (14 em `ux-advanced/`, 6 em `domain/`, 4 em `meta/`, 6 standalone). Total: 14 → 44.
- **v0.2.2:** 14 skills. Duplicatas que existiam em ambas foram mantidas na versão mais recente (geralmente a do framework) — ver `FRAMEWORK-STATUS.md > Seção A > v0.3.0`.
