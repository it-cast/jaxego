# Manual de Uso de Skills — gsd-framework

> **Quando consultar cada skill durante o fluxo gsd.**
>
> Skills são listadas por **momento de uso**, não por categoria. Use este manual ao planejar phase para garantir que está consultando as skills certas.

---

## Como ler este manual

| Ícone | Significado |
|---|---|
| 🔴 | **Obrigatória** — sem citação no PLAN.md, gate 3 bloqueia |
| 🟡 | **Recomendada** — ausente é warning, não bloqueio |
| 🟢 | **Opcional** — usar se contexto pedir |

---

## 📍 PHASE 0 — Bootstrap do projeto (`/gsd:bootstrap`)

Bootstrap é momento único do projeto. Skills aqui definem fundação.

### Discovery do produto
- 🔴 `meta/project-kickoff-interview` — entrevista estruturada com fundador
- 🔴 `meta/user-persona` — persona acionável (não genérica)
- 🟡 `meta/north-star-vision` — visão norte + métrica
- 🟡 `meta/competitive-analysis` — matriz comparativa
- 🟡 `meta/jobs-to-be-done` — para cada feature MVP, qual job?
- 🟢 `meta/journey-map` — se produto tem fluxo crítico não-trivial

### Decisões técnicas
- 🔴 `meta/stack-advisor` — escolha de stack
- 🟡 `meta/orchestration-decision-tree` — quando decompor em sub-tasks

### Métricas de produtividade
- 🔴 `meta/productivity-estimation` — capturar `estimated_solo_dev_weeks` em project.yaml

### Design system (se has_ui)
- 🔴 `quality/design-token-architecture` — estrutura dos tokens
- 🔴 `quality/spacing-system` — sistema de espaçamento
- 🔴 `quality/typography-scale` — escala tipográfica
- 🔴 `quality/color-system` — paleta + WCAG
- 🔴 `quality/layout-grid` — grid responsivo
- 🟡 `ux-advanced/design-tokens-system` — alto nível
- 🟡 `meta/refactoring-ui` — se sem designer dedicado

---

## 📍 PHASE — Discussão (`/gsd:discuss-phase N`)

Captura contexto e justificativa da phase.

### Sempre considerar
- 🟡 `meta/jobs-to-be-done` — phase atende qual job?
- 🟢 `meta/empathy-map` — se persona definida e pesquisa rasa
- 🟢 `meta/opportunity-framework` — se múltiplas opções de implementação
- 🟢 `meta/journey-map` — se phase atravessa múltiplos touchpoints

### Por tipo de phase
- **Feature nova:** 🔴 `meta/jobs-to-be-done`
- **Refactor:** 🟡 `quality/heuristic-evaluation` (avaliar antes), `meta/refactoring-ui`
- **Bugfix:** 🟡 `systematic-debugging`
- **Performance:** 🟡 `quality/performance-web-vitals`

---

## 📍 PHASE — UI/UX (`/gsd:ui-phase N`)

**Phase com `has_ui: true`. Gate 2 bloqueia se tokens.json ausente.**

### Sempre (toda phase com UI)
- 🔴 `ui-ux-pro-max` — direção estética (skill matriz)
- 🔴 `quality/accessibility-pro` — WCAG, ARIA, keyboard nav
- 🔴 `ux-advanced/design-tokens-system` — usar tokens, não hardcoded
- 🔴 `ux-advanced/empty-states-polish` — estados vazios
- 🔴 `ux-advanced/loading-states` — estados de carregamento

### Primeira phase com UI do projeto
- 🔴 `quality/design-token-architecture`
- 🔴 `quality/spacing-system`
- 🔴 `quality/typography-scale`
- 🔴 `quality/color-system`
- 🔴 `quality/layout-grid`
- 🔴 `product/component-library-governance` — não duplicar componentes

### Por contexto da phase

**Phase com formulários:**
- 🔴 `ux-advanced/form-ux-mastery`
- 🔴 `ux-advanced/feedback-patterns` — validação inline
- 🔴 `quality/error-ux-patterns` — mensagens de erro
- 🔴 `br/brazilian-forms` — máscaras pt-BR

**Phase com dashboard/analytics:**
- 🔴 `ux-advanced/saas-dashboard-patterns`
- 🔴 `ux-advanced/data-visualization` — escolha de gráfico
- 🟡 `ux-advanced/responsive-breakpoint-strategy`

**Phase com feed/lista/cards:**
- 🟡 `ux-advanced/loading-states` — skeletons
- 🟡 `ux-advanced/empty-states-polish`

**Phase com checkout/payment:**
- 🔴 `ux-advanced/payment-checkout-ux`
- 🔴 `ux-advanced/trust-safety-ux`
- 🔴 `domain/saas-billing-canonical`
- 🔴 `ux-advanced/feedback-patterns` — confirmações

**Phase com onboarding/signup:**
- 🔴 `ux-advanced/onboarding-patterns`
- 🟡 `meta/journey-map` — first-time experience

**Phase mobile (Ionic/Capacitor):**
- 🔴 `domain/ionic-patterns`
- 🔴 `ux-advanced/gesture-touch-patterns`
- 🟡 `mobile/offline-first` — se requer offline

**Phase com upload de arquivos:**
- 🔴 `ux-advanced/file-upload-ux`

**Phase com chat/mensagens:**
- 🔴 `ux-advanced/chat-ux-patterns`

**Phase com inputs avançados (datepicker, autocomplete):**
- 🟡 `ux-advanced/ui-input-rich-patterns`

**Phase com motion/animações:**
- 🟡 `product/micro-animations-delight`
- 🟡 `ux-advanced/motion-design-patterns`

**Phase com dark mode:**
- 🔴 `ux-advanced/dark-mode-theming`

### Quando designer entrega arte
- 🔴 `product/handoff-spec` — converter Figma em spec
- 🔴 `meta/design-to-code` — translation

### Sem designer dedicado
- 🔴 `meta/refactoring-ui` — princípios para não parecer amador

---

## 📍 PHASE — Research (`/gsd:research-phase N`)

Pesquisa técnica e de produto antes do plan.

### Sempre
- 🟡 `meta/empathy-map` — se persona definida

### Por tipo
- **Phase com auth/PII/endpoint:** 🔴 `owasp-security`
- **Phase com IA/LLM:** 🔴 `domain/llm-integration-patterns`, 🔴 `prompt-engineering`, 🟡 `spartan-ai-toolkit`
- **Phase com integração externa:** 🟡 `product/api-design-contracts`

---

## 📍 PHASE — Plan (`/gsd:plan-phase N`)

Plan-checker (gate 3) valida que skills citadas atendem contexto.

### Sempre citar em PLAN.md
- 🔴 As skills marcadas obrigatórias acima por contexto
- 🔴 Skills dispensadas com justificativa não-vazia em `## Skills Dispensadas`

### Plan deve incluir
- Lista de tasks (checklist)
- `## Skills Consultadas` (listadas com 1 frase do que vai aplicar)
- `## Success Criteria` (testáveis)
- `## Risks` (top 3)

---

## 📍 PHASE — Execução (`/gsd:execute-phase N`)

Implementação real do código.

### Sempre
- 🔴 Skills citadas no PLAN.md devem ser CONSULTADAS antes de codar (Regra 5 do CLAUDE.md)
- 🔴 `quality/observability-production` — se phase tem endpoint/job

### Por contexto
- **Phase backend Python:** 🔴 `domain/mysql-schema-design` se DB
- **Phase com Docker:** 🔴 `domain/docker-production-ready`
- **Phase Angular:** 🔴 `domain/angular-material-patterns`
- **Phase com testes:** 🔴 `webapp-testing` (E2E), unitários sempre

---

## 📍 PHASE — Verificação (`/gsd:verify-work N`)

UAT conversacional + audit.

### Sempre (se has_ui)
- 🔴 `quality/heuristic-evaluation` — Nielsen heuristics
- 🔴 `quality/accessibility-pro` — WCAG audit

### Por tipo
- **Phase de feature:** UAT conversacional + heuristic-eval
- **Phase de bugfix:** `systematic-debugging` — root cause analysis

---

## 📍 PHASE — Métricas (`/gsd:metrics N`)

Captura métricas + gera retro.

- 🔴 Auto-retro com 5 campos qualitativos
- 🔴 Entrada em METRICS.md com `duration_hours` (alimenta productivity-estimation)

---

## 📍 MILESTONE — Audit (`/gsd:audit-milestone`)

Audit consolidado do milestone.

- 🔴 `meta/productivity-estimation` — calcula ganho vs solo-dev
- 🔴 `quality/heuristic-evaluation` — audit consolidado UI
- 🟡 `quality/observability-production` — verificar logs/traces estão em produção

---

## 📍 MILESTONE — Summary (`/gsd:milestone-summary`)

Sumário final.

- 🔴 `meta/productivity-estimation` — relatório de ganho

---

## 🚫 Phases SEM UI

Pular skills de UI/design system. Foco em:
- 🔴 `domain/*` por stack
- 🔴 `quality/observability-production` se tem endpoint
- 🔴 `owasp-security` se tem auth/PII
- 🔴 `webapp-testing` se tem E2E

---

## 📋 Checklist rápido por contexto

```
[ ] Brasileiro (locale=pt-BR)?
    → br/brazilian-forms, br/lgpd-compliance, br/ux-copywriting-ptbr

[ ] Mobile (has_mobile=true)?
    → domain/ionic-patterns, ux-advanced/gesture-touch-patterns

[ ] Tem DB (MySQL)?
    → domain/mysql-schema-design

[ ] Tem AI/LLM?
    → domain/llm-integration-patterns, prompt-engineering

[ ] Tem billing/subscription/payment?
    → domain/saas-billing-canonical, ux-advanced/payment-checkout-ux,
      ux-advanced/trust-safety-ux

[ ] Tem auth/PII?
    → owasp-security, br/lgpd-compliance

[ ] Tem dashboards/analytics?
    → ux-advanced/saas-dashboard-patterns, ux-advanced/data-visualization

[ ] Tem multi-idioma?
    → quality/i18n-ready-architecture

[ ] Tem dark mode?
    → ux-advanced/dark-mode-theming

[ ] Phase com UI?
    → ui-ux-pro-max + quality/accessibility-pro + design-tokens
```

---

## 🎯 Regra ouro

Se em dúvida sobre quais skills citar, no `/gsd:plan-phase` peça:

```
"Antes de gerar o PLAN.md, consulte SKILLS-USAGE-MANUAL.md.
Para o contexto desta phase ([resumo da phase]), liste TODAS
as skills aplicáveis com justificativa."
```

O plan-checker (gate 3, Dimension 6) vai validar contra `triggers.yaml` de cada skill citada.

---

## 📊 Catálogo numérico

- **Skills totais (v0.9.4):** 64
- **Categorias:**
  - `meta/`: 11 (estratégia, discovery)
  - `quality/`: 11 (design system + observability + heurísticas)
  - `ux-advanced/`: 17 (UX patterns avançados)
  - `domain/`: 6 (stack-específicas)
  - `product/`: 4 (governance, governança)
  - `br/`: 3 (Brasil)
  - `mobile/`: 2
  - `standalone`: 6 (matriz, security, AI, debug, testing)

---

## ⚠️ Anti-patterns ao usar skills

❌ Citar skill sem aplicar (gate 3 valida citação, não aplicação)
❌ Dispensar skill obrigatória sem justificativa concreta
❌ Plan sem `## Skills Consultadas`
❌ Aplicar skill que não está no contexto (over-engineering)
❌ Reler skill toda vez (consultar 1x no início da phase, internalizar)

---

**Atualizado em:** 2026-04-28 (v0.9.4)
**Mantenedor:** ver INDICE-MESTRE.md

---

## 🌟 Skills com densidade reforçada (v0.9.4)

As 6 skills abaixo passaram por densificação completa em v0.9.4 — incluem templates copy-paste, exemplos completos em 5+ domínios, snippets de código React/Angular, anti-patterns com correção lado a lado, e checklists de validação extensos. Use estas como **referência primária** quando aplicáveis:

### `meta/jobs-to-be-done` (801 linhas)
- Switch interview de Bob Moesta (roteiro completo)
- Outcome-Driven Innovation com fórmula de opportunity score
- 5 JTBDs completos: Áugure, iFood, Slack, Stripe, Notion
- Templates de discovery, validation, pitch
- Como JTBD vira input para journey-map, persona, opportunity-framework

### `meta/user-persona` (846 linhas)
- Distinção clara persona-acionável vs persona-ornamental
- Estrutura YAML completa com 17 campos por persona
- Roteiro de entrevista 60-90 min em 6 blocos
- Persona priorization matrix com scoring
- 5 personas exemplo + anti-personas explícitas
- Plano de evolução por stage do produto

### `quality/color-system` (994 linhas)
- 6 paletas hex prontas (slate, neutral, stone + brand colors)
- Tabelas de contraste WCAG pré-validadas (combinações testadas)
- Dark mode completo com swap automático
- Daltonismo: combinações safe + ferramentas
- Implementação completa CSS + tokens.json
- 5 contextos (SaaS, B2C, fintech, health, Áugure)

### `quality/heuristic-evaluation` (940 linhas)
- 10 heurísticas de Nielsen com checklists específicos cada
- Severity scale Nielsen (0-4) com critério de decisão
- Templates: quick eval (30min), full eval (2-4h), comparative
- Checklists por contexto (e-commerce, SaaS, mobile, form longo)
- 2 exemplos completos de findings (Áugure, SaaS billing)
- Como rodar com Claude (prompt pronto)

### `ux-advanced/loading-states` (798 linhas)
- 4 níveis: spinner, skeleton, progressive, optimistic
- Snippets React + Angular 19 (signals + resource API) + Ionic
- Matriz completa de decisão por contexto (20+ situações)
- Tempos perceptuais com decisão UX
- Loading vs empty vs error (não confundir)
- Anti-patterns clássicos com correção

### `meta/refactoring-ui` (881 linhas)
- 7 princípios essenciais com snippets CSS prontos
- 6 truques específicos (sombras camadas, estados, forms, cards, botões, tipografia)
- 8 anti-patterns AI-slop com correção lado a lado
- 2 antes/depois UI real (login, card de produto)
- Stack visual recomendado (decisões prontas)
- Checklist anti-AI-slop com 20+ itens
- Inspirações de UIs profissionais (Linear, Stripe, Nubank, etc.)

**Próximas (v0.9.4 e além):** outras 12 skills do batch externo serão densificadas conforme uso real revelar prioridade.

