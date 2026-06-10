# PLAN — Phase 3 Plan 01-06: Shell frontend + design system (3 superfícies)

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Entregar o **shell frontend** e o **design system** do Jaxegô como base das 3 superfícies (entregador mobile-first / loja web responsivo / admin desktop-first), num único app Angular 19 standalone + Ionic 8 + Capacitor 6: scaffold `apps/web`, build step `tokens.json → CSS vars` (tema claro + dark), sistema de tema (toggle + `prefers-color-scheme` + anti-FOUC), componentes de estado canônicos (REQ-055), tipografia, tela de **login** conectada a `/v1/auth/login`, e shell navegável das 3 superfícies (esqueleto + guarda de rota). **Sem** cadastro, dashboards ou entrega.

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] `apps/web` builda: `pnpm -C apps/web build` retorna 0; bundle `main` ≤ 400KB gzip (config.json), lazy chunk por superfície gerado (DRV-004).
- [ ] **Zero cor hardcoded fora da geração de tokens:** `grep -rE "#E84E1B|#FAF6EE" apps/web/src --include="*.scss" | grep -v _tokens.scss` → 0 ocorrências.
- [ ] `_tokens.scss` é **gerado** por script Node a partir de `tokens.json` (não escrito à mão); regenerar é idempotente (`git diff` vazio após rerun).
- [ ] As 21 vars semânticas (§1.3 do UI-SPEC) existem para os dois temas; tokens dark presentes derivados de `tokens.json` (DEC-001).
- [ ] Alternância claro↔escuro funcional (toggle + `prefers-color-scheme`), persistida em `localStorage('jx-theme')`, **sem FOUC** (atributo `data-theme` aplicado antes do primeiro paint).
- [ ] Contraste AA nos dois temas (axe + verificação de pares `--text`/`--surface`, `--brand-contrast`/`--brand`).
- [ ] `axe-core` na tela de login: zero violações críticas (CI gate `a11y_axe_required`).
- [ ] Login conecta a `POST /v1/auth/login` (dev proxy → :8000): 200 emite redireciono, 401 mostra erro anti-enumeração, `totp_required` revela campo TOTP.
- [ ] Guarda de rota redireciona não-autenticado para `/entrar`; 3 superfícies navegáveis (esqueleto).
- [ ] Componentes `jx-empty-state` / `jx-error-state` / `jx-loading-skeleton` / `jx-warn-banner` existem em `shared/`, token-driven, com a11y correta (REQ-055).
- [ ] Todos os testes relacionados passam (`pnpm -C apps/web test`).
- [ ] Lint limpo (`pnpm -C apps/web lint`).
- [ ] Commit atômico por wave com mensagem padronizada `feat(phase-3/...)`.

## REQs referenciados

- **REQ-056** — tokens/voz/vocabulário em toda copy (claro + escuro, DEC-001) — Tasks T-02, T-03, T-04, T-05.
- **REQ-055** — componentes de estado obrigatórios (empty / error / loading / warn) — Task T-04.
- **REQ-005** (camada UI) — tela 01-login conectada a `/v1/auth/*` — Task T-05.

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a uma ou mais tasks deste plano.

- `meta/orchestration-decision-tree` — T-01: phase de UI com 6 tasks sequenciais em 6 waves (scaffold → tokens/tema → componentes de estado → login → shell/rotas → testes/baseline); execução inline (sem squad de execução paralela), pois há forte dependência de arquivos compartilhados (`_tokens.scss`, `theme.service`, `shared/`). parallel-hint conservador.
- `ux-advanced/design-tokens-system` — T-02: camada primitiva (`tokens.json` → `--jx-*` gerada) → camada semântica (21 vars `--surface`/`--text`/`--brand`…) → uso. Componentes consomem **só** a camada semântica, nunca o primitivo. Build step gera, não escreve à mão.
- `ux-advanced/dark-mode-theming` (DEC-001) — T-03: dois temas por troca de CSS vars em `:root` / `:root[data-theme="dark"]`; precedência `localStorage → prefers-color-scheme → claro`; **anti-FOUC** com script síncrono inline no `<head>` antes do bootstrap; warm preservado no dark (sombras `rgba(24,20,16,…)`, brand sobe para `brand.400`).
- `ux-advanced/design-tokens-system` + `ui-ux-pro-max` — T-03: tipografia editorial-técnica (Inter Tight / Fraunces italic 1 palavra-chave por título / JetBrains Mono em dados); NADA de gradiente genérico, glassmorphism ou laranja neon; persimmon queimado + cream warm.
- `product/component-library-governance` — T-04: componentes de estado canônicos compartilhados em `shared/`, reusados em todas as telas dali em diante; baseline de visual regression (stories claro+dark) criado nesta phase (não comparação ainda).
- `ux-advanced/empty-states-polish` — T-04: `jx-empty-state` com causa + ação, nunca "Lista vazia" ("Nenhuma entrega ainda. Crie a primeira no botão acima.").
- `quality/error-ux-patterns` — T-04, T-05: `jx-error-state` `role="alert"`, WarnBanner não-bloqueante `role="status"`, mensagem = o que houve + o que fazer; nunca "Algo deu errado".
- `br/ux-copywriting-ptbr` — T-04, T-05: sentence case, CTA verbo+objeto ≤4 palavras sem ponto ("Entrar"), erro acionável, anti-enumeração no login ("E-mail ou senha incorretos…"), vocabulário do glossário (entregador/loja).
- `quality/accessibility-pro` — T-03, T-04, T-05, T-06: contraste AA nos dois temas, foco visível (`--focus-ring`), touch ≥44px no mobile, labels em todo input, live regions (`role=alert`/`status`/`aria-busy`), landmarks (`<main>`/`<nav>`/`aria-current`), `prefers-reduced-motion`.
- `ux-advanced/responsive-breakpoint-strategy` — T-06: mobile-first (entregador, ≤420px), responsivo fluido (loja, 620–860px), desktop-first (admin, sidebar densa) num só codebase; safe-area insets no mobile.
- `domain/ionic-patterns` — T-01, T-06: scaffold Ionic 8 + Capacitor 6; shell do entregador com `ion-tabs` (tabbar inferior), `ion-content`; OnPush + standalone.
- `domain/angular-material-patterns` — T-01, T-06: organização Angular standalone (core/shared/features/layouts), padrões de a11y/estrutura de layout (landmarks, foco) — observação: styling é **SCSS + CSS vars de tokens** (D-02/DRV-008), não Material theming nem Tailwind; Material entra só como padrão de estrutura/comportamento de componente quando útil.
- `quality/observability-production` — T-05: `request_id` do envelope de erro (`{error:{code,message,request_id}}`) logado no client (console/telemetria), **nunca** exibido cru ao usuário (só fallback técnico). Zero PII em log de frontend (sem email/senha/token no console).
- `quality/senior-quality-bar` (Gate 8) — todas as tasks: zero segredo no repo (sem token em localStorage — access em memória, refresh em cookie httpOnly do backend), zero `outline:none` sem substituto, decisão de auth explícita (guarda de rota), sem cor hardcoded.

## Skills Dispensadas (com justificativa)

- `domain/saas-billing-canonical` / `domain/safe2pay-escrow-br` — `has_payments: false` nesta phase; nenhum fluxo de cobrança/assinatura/checkout. Entram na phase de billing.
- `mobile/offline-first` — sem dados de negócio ainda; shell é só esqueleto navegável, não há cache de dados offline para gerir nesta phase.
- `mobile/push-notifications-architecture` — sem push nesta phase (notificações entram com entregas/tracking).
- `ux-advanced/data-tables-ux` / `ux-advanced/saas-dashboard-patterns` — sem tabelas, listas de negócio ou dashboards nesta phase (só placeholders de shell). Entram nas phases de loja/admin.
- `ux-advanced/form-ux-mastery` / `br/brazilian-forms` — o login é um form **simples** (2–3 campos, sem máscaras CNPJ/CPF/telefone, sem wizard, sem validação BR composta). Validação aplicada é mínima (required, email, minlength 10, anti-enumeração) e coberta por `error-ux-patterns` + `ux-copywriting-ptbr`. Form mastery completo entra na Phase 4/5 (cadastro).
- `ux-advanced/gesture-touch-patterns` — sem gestos (swipe/drag/pull-to-refresh) nesta phase; só navegação por toque padrão (coberto por touch ≥44px de `accessibility-pro`). Entra na Phase 5 (mobile do entregador).
- `product/micro-animations-delight` / `ux-advanced/motion-design-patterns` — `has_non_trivial_motion: false`. Único motion: transição de tema, press do botão (scale .97) e pulse do skeleton — todos tokenizados (`motion.*`) e dentro de `prefers-reduced-motion`, sem coreografia não-trivial.
- `ux-advanced/onboarding-patterns` — o login **não** é onboarding (sem signup, sem tour, sem progressive disclosure de cadastro). É autenticação de usuário existente. Onboarding entra na Phase 4/5 (cadastro de loja/entregador).
- `ux-advanced/trust-safety-ux` — sem PII coletada/exibida e sem decisão de risco do usuário nesta phase (login só autentica). Anti-enumeração já coberto por `error-ux-patterns`/`ux-copywriting-ptbr`. Entra na Phase 5 (KYC/documentos).
- `ux-advanced/dark-mode-theming` está **consultada** (não dispensada) — DEC-001 a torna obrigatória.

---

## Tech debt deste plano (verificação obrigatória v0.8+)

Consultado `.planning/TECH-DEBT.md`: nenhum item com `Prazo (Phase)` igual a esta phase nem `urgency_class: pre_launch_*` aplicável (esta phase não é a última antes do launch — `is_pre_release: false`).

**N/A — TECH-DEBT.md não tem itens com prazo nesta phase.**

| TD ID | Descrição curta | Por que entra (ou não) | Task |
|-------|-----------------|------------------------|------|
| — | — | nenhum TD com prazo Phase 3 | — |

Possíveis dívidas geradas nesta phase (registrar em execução, não pré-existentes):
- Visual regression é **baseline only** (sem comparação automática ainda) — deferido até haver baseline de componentes compartilhados (CONTEXT §deferred). Registrar TD com `urgency_class: post_launch_quarter` se a comparação não entrar até a próxima phase de UI.

---

## Open questions / LOW confidence do RESEARCH

Esta phase não teve RESEARCH.md dedicado (UI-SPEC + CONTEXT cobrem o contrato de design). Open questions do **UI-SPEC §10** viram decisão consciente:

| Item | Confidence | Resolução neste plano |
|------|------------|------------------------|
| Logo: 100% tipográfica ou gráfico? (UI-SPEC §10) | MED | T-05: seguir 100% tipográfica ("Jaxegô. Chegou *rapidinho.*"); shell sem logo gráfico. Decisão consciente — confirmar com humano antes de phases com header de marca. |
| `--surface-elevated` claro = `neutral.100` vs `#fff` (UI-SPEC §10) | MED | T-02: usar `neutral.100` (#F2EBE0) para manter 100% tokenizado e warm (não inventar `#fff` em CSS). Se humano quiser branco puro, adicionar `neutral.0` em `tokens.json` (decisão consciente, fora desta phase). |

---

## Threat model

Esta phase **consome** auth existente (`/v1/auth/*` da Phase 2) e **não introduz** novo endpoint, novo armazenamento de PII, nem nova superfície de ataque server-side. Risco de auth avaliado e mitigado no cliente:

- **Token em memória** (signal/serviço), **refresh em cookie httpOnly + Secure + SameSite=strict** (já setado pelo backend) — nenhum token em `localStorage` (Gate 8 / A05).
- **Anti-enumeração** preservada: frontend exibe `error.message` do backend (já genérico), nunca decide "email existe?".
- **`request_id`** logado em telemetria do client, nunca exposto cru ao usuário.

**N/A (novo risco) — este plano não cria endpoint, autenticação ou armazenamento de PII; apenas consome auth existente da Phase 2. Risco de manuseio de token no client avaliado e mitigado acima.**

| ID | Ameaça | Vetor | Mitigação | Task |
|----|--------|-------|-----------|------|
| TH-01 | Roubo de token via XSS | token em localStorage | access em memória; refresh em cookie httpOnly (backend) | T-05/T-06 |
| TH-02 | Enumeração de e-mail | mensagem de erro distinta | exibir `error.message` genérico do backend | T-05 |

---

## Performance budget (TEM UI)

Herdado de `.planning/config.json > performance_budget`:

**Frontend:**
- LCP ≤ 2500ms (4G) — tela de login leve, fontes com `font-display: swap`, sem render-blocking além do script anti-FOUC (microscópico).
- INP ≤ 200ms
- CLS ≤ 0.1 — login sem layout shift: loading mantém botão "Entrar" desabilitado (sem trocar texto) + skeleton ocupa espaço reservado.
- Bundle `main.js` ≤ 400KB gzip; vendor ≤ 800KB gzip.
- **Lazy loading:** cada superfície (`/entregador`, `/loja`, `/admin`) em chunk lazy (DRV-004); `/entrar` no bundle inicial.
- **Zero FOUC de tema:** `data-theme` aplicado por script síncrono inline antes do primeiro paint (UI-SPEC §1.2).

Ferramenta: Lighthouse CI no pipeline (LCP/CLS/bundle), `axe-core` para a11y.

---

## Observability checklist

**N/A — este plano é frontend-only; não cria endpoint nem background job.**

Único ponto de observabilidade do client (T-05):
- [x] `request_id` do envelope de erro (`{error:{code,message,request_id}}`) registrado em telemetria/console do client para correlação — nunca exibido cru.
- [x] **Zero PII em log de frontend:** sem `email`/`password`/`token` em console ou telemetria (config.json `pii_fields_forbidden_in_logs`).

---

## Error UX checklist (TEM UI)

Aplicando `quality/error-ux-patterns` + `br/ux-copywriting-ptbr`:

- [ ] **Credencial inválida (anti-enumeração):** "E-mail ou senha incorretos. Tente de novo ou recupere a senha." — `jx-error-state` `role="alert"`, foco move ao alerta. Nunca revelar se e-mail existe (RN-011/ADR-005).
- [ ] **Erro de rede:** "Sem conexão com o servidor. Verifique sua internet e tente de novo." + retry.
- [ ] **Erro de servidor (5xx):** "Tivemos um problema aqui. Já estamos vendo — tente em instantes." + retry.
- [ ] **TOTP requerido** (`error.code = totp_required`): revela campo "Código de verificação", `aria-live="polite"`, copy "Digite o código do seu app autenticador."
- [ ] Validação inline (required/email/minlength) ao blur, não modal ao submit.
- [ ] **404 customizado:** rota inexistente → `jx-empty-state` "Página não encontrada." + CTA "Voltar ao início".
- [ ] Decisão consistente: erro de login = **inline** (`jx-error-state`); aviso não-bloqueante = `jx-warn-banner`; nunca toast festivo em sucesso (redireciona).

---

## Integration contracts

**N/A — `integration_check: false` no ROADMAP.** O login consome `/v1/auth/login` da Phase 2 via dev proxy; contrato exato documentado em T-05 (verificado por teste de client, não por `gsd-integration-checker`).

Contrato consumido (referência):
- `POST /v1/auth/login` body `{ email, password, totp? }` → 200 `{ access_token, refresh_token, token_type, expires_in }` + cookie `refresh_token` httpOnly. Erro `{ error: { code, message, request_id } }`; `code = "totp_required"` sinaliza 2FA.

---

## Tasks

### T-01 — Scaffold `apps/web` (Angular 19 standalone + Ionic 8 + Capacitor 6)

- **Type:** infra
- **Files:** `apps/web/package.json`, `apps/web/angular.json`, `apps/web/tsconfig*.json`, `apps/web/ionic.config.json`, `apps/web/capacitor.config.ts`, `apps/web/src/main.ts`, `apps/web/src/app/app.config.ts`, `apps/web/src/app/app.routes.ts`, `apps/web/src/index.html`, `apps/web/.eslintrc / eslint.config.*`, `apps/web/proxy.conf.json`, `apps/web/src/{core,shared,features,layouts}/.gitkeep`
- **Skills aplicadas:**
  - `domain/ionic-patterns` — Ionic 8 + Capacitor 6, standalone, `provideIonicAngular`.
  - `domain/angular-material-patterns` — estrutura standalone `core/shared/features/layouts`, OnPush default, signals; sem Tailwind/Material theming (styling via SCSS + CSS vars, D-02).
  - `meta/orchestration-decision-tree` — base do app antes de qualquer feature; demais tasks dependem desta.
- **Descrição:** Scaffold do app Angular 19 standalone com Ionic 8 e Capacitor 6 em `apps/web` (ao lado de `apps/api`). Node 22, pnpm. Configurar: control flow novo (@if/@for), OnPush como default, signals, `provideRouter` com lazy routes, ESLint + lint script, `proxy.conf.json` roteando `/v1/*` → `http://localhost:8000`. `index.html` com `lang="pt-BR"` e placeholder do script anti-FOUC (preenchido em T-03). Estrutura de pastas `core/` (guards, services, http), `shared/` (componentes de estado, tokens), `features/` (placeholder por superfície), `layouts/` (3 shells).
- **Success:** `pnpm -C apps/web install` ok; `pnpm -C apps/web build` retorna 0; `pnpm -C apps/web lint` limpo; árvore `core/shared/features/layouts` existe; `proxy.conf.json` aponta `/v1` → :8000.
- **Estimate:** ~15% contexto.
- **Depends on:** none.

### T-02 — Build step `tokens.json → _tokens.scss` (camada primitiva + 21 vars semânticas claro/dark)

- **Type:** infra
- **Files:** `tooling/tokens/build-tokens.mjs` (ou `apps/web/scripts/build-tokens.mjs`), `apps/web/src/styles/_tokens.scss` (GERADO), `apps/web/src/styles/_semantic.scss`, `apps/web/src/styles/global.scss`, `apps/web/package.json` (script `tokens:build` + prebuild hook)
- **Skills aplicadas:**
  - `ux-advanced/design-tokens-system` — camada primitiva `--jx-*` gerada de `tokens.json`; camada semântica (21 vars) definida sobre primitivos; componentes consomem só a semântica.
  - `ux-advanced/dark-mode-theming` — dark reusa `neutral.600–900` e `brand.300/400/800/900`; mapeamento por tema (UI-SPEC §1.3), zero hex inventado (Gate 2).
  - `quality/senior-quality-bar` — geração determinística (idempotente), zero cor hardcoded fora do gerado.
- **Descrição:** Script Node (`build-tokens.mjs`) lê `docs/identidade-visual/tokens.json` e gera `_tokens.scss` com **todas** as primitivas `--jx-*` (cores brand/neutral/semantic, spacing 1–9, radius, font.*, shadow.*, motion.*). Hook `prebuild`/`prestart` regenera. Em `_semantic.scss` (escrito à mão, mas consumindo SÓ primitivas), definir as **21 vars semânticas** da UI-SPEC §1.3 em `:root` (claro) e `:root[data-theme="dark"]` (dark), mais sombras/foco (§1.4) iguais nos dois temas. Cada var aponta para uma `--jx-*` (ex.: `--surface: var(--jx-neutral-50)` claro, `var(--jx-neutral-900)` dark; `--brand: var(--jx-brand-500)` claro, `var(--jx-brand-400)` dark). Nenhum `#hex` literal em `_semantic.scss`.
- **Success:** `pnpm -C apps/web tokens:build` gera `_tokens.scss` idempotente (rerun → `git diff` vazio); as 21 vars existem em ambos os blocos de tema; `grep -rE "#E84E1B|#FAF6EE" apps/web/src --include="*.scss" | grep -v _tokens.scss` → 0 ocorrências.
- **Estimate:** ~20% contexto.
- **Depends on:** T-01.

### T-03 — Sistema de tema (toggle + prefers-color-scheme + anti-FOUC) + tipografia

- **Type:** ui_component
- **Files:** `apps/web/src/index.html` (script síncrono inline), `apps/web/src/core/theme/theme.service.ts`, `apps/web/src/core/theme/theme-toggle.component.ts`, `apps/web/src/styles/typography.scss`, `apps/web/src/core/theme/theme.service.spec.ts`
- **Skills aplicadas:**
  - `ux-advanced/dark-mode-theming` — precedência `localStorage('jx-theme') → prefers-color-scheme → claro`; script síncrono inline no `<head>` aplica `data-theme` antes do paint (anti-FOUC); `ThemeService` (signal) lê/escreve mesmo atributo + chave após bootstrap; `theme-toggle` com `aria-pressed`, label "Tema escuro".
  - `ui-ux-pro-max` — direção editorial-técnica: Inter Tight (UI), Fraunces italic 1 palavra-chave/título cor `--brand`, JetBrains Mono em dados; sem gradiente/glassmorphism/laranja neon.
  - `quality/accessibility-pro` — foco visível (`--focus-ring`), `prefers-reduced-motion` desliga transição de tema/loop.
- **Descrição:** Adicionar script síncrono inline no `<head>` do `index.html` (UI-SPEC §1.2) que resolve o tema e aplica `data-theme` antes do bootstrap. `ThemeService` baseado em signal: estado `'light'|'dark'`, métodos `set`/`toggle`, persiste em `localStorage`, escuta `prefers-color-scheme`. `ThemeToggleComponent` standalone (botão `aria-pressed`, touch ≥44px). `typography.scss` define escala/famílias/pesos da UI-SPEC §2 via tokens (helper `.jx-italic-accent` para Fraunces italic em `--brand`). Transição de tema com `motion.normal`, respeitando `prefers-reduced-motion`.
- **Success:** alternância claro↔escuro funcional e persistida; recarregar com `jx-theme=dark` no localStorage NÃO mostra flash claro (teste manual + verificação live no T-06); `theme.service.spec` passa (precedência + toggle); zero `outline:none` sem `--focus-ring`.
- **Estimate:** ~20% contexto.
- **Depends on:** T-02.

### T-04 — Componentes de estado canônicos (REQ-055): EmptyState / ErrorState / LoadingSkeleton / WarnBanner

- **Type:** ui_component
- **Files:** `apps/web/src/shared/state/empty-state.component.ts`, `error-state.component.ts`, `loading-skeleton.component.ts`, `warn-banner.component.ts` (+ `.scss` co-locados), `apps/web/src/shared/state/index.ts`, specs por componente, stories de baseline visual `apps/web/src/shared/state/*.stories.ts`
- **Skills aplicadas:**
  - `product/component-library-governance` — componentes compartilhados em `shared/`, API de inputs consistente, baseline de visual regression (stories claro+dark) criado aqui.
  - `ux-advanced/empty-states-polish` — `jx-empty-state` causa + ação, CTA opcional, nunca "Lista vazia"; `role="status"`.
  - `quality/error-ux-patterns` — `jx-error-state` `role="alert"` + retry; `jx-warn-banner` não-bloqueante `role="status"` + dispensar.
  - `br/ux-copywriting-ptbr` — copy padrão pt-BR (sentence case, acionável, vocabulário do glossário).
  - `quality/accessibility-pro` — live regions corretas; skeleton `aria-hidden` + container `aria-busy`; `prefers-reduced-motion` → pulse estático; touch ≥44px em botões.
- **Descrição:** 4 componentes standalone OnPush, token-driven (só vars semânticas §1.3), conforme UI-SPEC §4:
  - `jx-empty-state` (`@Input` title/message/ctaLabel/icon) — `role="status"`.
  - `jx-error-state` (`@Input` message/retryLabel, `@Output` retry) — `role="alert"`, fundo `--error-bg`, borda esq 3px `--error`.
  - `jx-loading-skeleton` — primitivos `line`/`block`/`circle` + composição; pulse `@keyframes` 1.2s; `aria-hidden`, container `aria-busy`.
  - `jx-warn-banner` (`@Input` message/dismissible, `@Output` dismiss) — `role="status"`, fundo `--warning-bg`, borda esq 3px.
  Stories de baseline (default/variações × claro+dark) por UI-SPEC §9.
- **Success:** 4 componentes renderizam nos dois temas; specs de a11y passam (roles corretos, `aria-busy`, labels); axe sem violações críticas nos stories; nenhum `#hex` literal nos `.scss`.
- **Estimate:** ~25% contexto.
- **Depends on:** T-03.

### T-05 — Tela de Login conectada a `/v1/auth/login` (idle/loading/erro/TOTP)

- **Type:** ui_component
- **Files:** `apps/web/src/core/auth/auth.service.ts`, `apps/web/src/core/auth/auth.guard.ts`, `apps/web/src/core/auth/auth.models.ts`, `apps/web/src/features/auth/login.page.ts` (+ `.scss`), `apps/web/src/features/auth/login.page.spec.ts`, `apps/web/src/features/auth/login.stories.ts`
- **Skills aplicadas:**
  - `br/ux-copywriting-ptbr` — copy do wireframe: header "Jaxegô. Chegou *rapidinho.*", botão "Entrar", erro anti-enumeração.
  - `quality/error-ux-patterns` — estados de erro inline (credencial/rede/servidor), TOTP `aria-live`, sem layout shift no loading.
  - `quality/accessibility-pro` — foco inicial no e-mail, foco move ao alerta, labels `for`, toggle senha `aria-label`, touch ≥44px, foco visível.
  - `ui-ux-pro-max` — Fraunces italic só em "rapidinho.", layout editorial centrado, sem festa visual.
  - `quality/observability-production` — `request_id` do erro logado em telemetria, nunca exibido cru; zero PII no log.
  - `quality/senior-quality-bar` — **access token em memória (signal), refresh em cookie httpOnly** (nunca localStorage); decisão de auth explícita.
- **Descrição:** `AuthService` (signal de `accessToken` em memória; `login(email,password,totp?)` chama `POST /v1/auth/login`; em sucesso guarda access em memória e redireciona pela superfície do usuário; refresh fica no cookie httpOnly do backend). `auth.models.ts` tipa `TokenPair {access_token, refresh_token, token_type, expires_in}` e o envelope de erro `{error:{code,message,request_id}}`. `authGuard` functional. `LoginPage` standalone reproduz o wireframe `01-login.html` com tokens semânticos: campos e-mail (`inputmode=email`, `autocomplete=email`) / senha (`minlength=10`, `autocomplete=current-password`, toggle mostrar/ocultar) / TOTP **condicional** (revelado quando resposta tem `error.code = "totp_required"`, `inputmode=numeric`, `autocomplete=one-time-code`, fonte mono). Estados: idle (foco e-mail) / loading (botão desabilitado + skeleton, sem trocar texto, `aria-busy`) / erro (`jx-error-state` `role=alert`, foco ao alerta) / TOTP (revela campo `aria-live=polite`) / sucesso (redireciona). Sem token em localStorage.
- **Success:** com dev proxy + API :8000 (ou mock): 200 redireciona; 401 mostra "E-mail ou senha incorretos…"; `totp_required` revela campo TOTP e reenvia com `totp`; erro de rede mostra mensagem de rede. `login.page.spec` cobre os 4 estados. `axe` na login: zero violações críticas. Nenhum `localStorage.setItem` de token (grep). Fraunces italic só em "rapidinho.".
- **Estimate:** ~30% contexto.
- **Depends on:** T-04.

### T-06 — Shell das 3 superfícies (esqueleto + guarda de rota + lazy) e verificação visual/build

- **Type:** ui_component
- **Files:** `apps/web/src/layouts/entregador-shell.component.ts` (Ionic tabs), `loja-shell.component.ts`, `admin-shell.component.ts` (+ `.scss`), `apps/web/src/app/app.routes.ts` (lazy + guard + 404), `apps/web/src/features/*/placeholder.page.ts`, `apps/web/src/shared/not-found.page.ts`, specs de rota/guarda
- **Skills aplicadas:**
  - `ux-advanced/responsive-breakpoint-strategy` — entregador mobile-first (`ion-tabs`, ≤420px, safe-area), loja 620–860px responsivo, admin desktop-first (sidebar densa).
  - `domain/ionic-patterns` — `ion-tabs` + tabbar inferior (Início/Entregas/Ganhos/Perfil), `aria-current="page"` na aba ativa.
  - `domain/angular-material-patterns` — layouts standalone, lazy routes, landmarks (`<main>`/`<nav>`).
  - `quality/accessibility-pro` — landmarks, `aria-current`, touch ≥44px nas abas/toggle, foco visível.
  - `ux-advanced/empty-states-polish` / `quality/error-ux-patterns` — placeholders usam `jx-empty-state`; 404 usa `jx-empty-state` ("Página não encontrada." + CTA "Voltar ao início").
  - `quality/observability-production` — N/A backend; verificação de bundle/lazy aqui.
- **Descrição:** 3 layouts standalone (esqueleto navegável, sem telas de negócio): entregador (`ion-tabs` com 4 abas placeholder usando `jx-empty-state`), loja (topbar + slot de rota com placeholder), admin (sidebar colapsável + slot). Theme toggle (`ThemeToggleComponent`) presente em cada shell (perfil/topbar/sidebar). `app.routes.ts`: `/entrar` pública; `/entregador/**`, `/loja/**`, `/admin/**` **lazy** + protegidas por `authGuard` (redireciona não-autenticado para `/entrar`); rota wildcard → `not-found.page` (`jx-empty-state`). Pós-login redireciona pela superfície do usuário. Verificação visual/build final: `ng build` + smoke de navegação (Playwright/axe headless) capturando screenshot das telas-chave nos dois temas (baseline §9), confirmando ausência de FOUC.
- **Success:** `pnpm -C apps/web build` gera chunk lazy por superfície; bundle `main` ≤ 400KB gzip; guarda redireciona não-autenticado para `/entrar` (spec); 3 shells navegáveis; 404 mostra `jx-empty-state`; axe nas telas-chave sem violações críticas; screenshots de baseline (claro+dark) capturados sem flash de tema. `pnpm -C apps/web test` e `lint` verdes.
- **Estimate:** ~25% contexto.
- **Depends on:** T-05.

---

## Execution order

Waves (parallel-hint conservador — forte dependência de arquivos compartilhados, execução sequencial inline):

- **Wave 1:** T-01 (scaffold `apps/web`).
- **Wave 2:** T-02 (build de tokens → CSS vars; depende do scaffold).
- **Wave 3:** T-03 (tema + tipografia; depende das vars).
- **Wave 4:** T-04 (componentes de estado; depende do tema/tipografia).
- **Wave 5:** T-05 (login; depende dos componentes de estado + tokens).
- **Wave 6:** T-06 (shell + rotas + verificação visual/build; depende do login e do auth.service/guard).

> Não há checkpoint humano bloqueante: a verificação visual (build + screenshot axe headless nos dois temas, anti-FOUC) está embutida como **verificação automatizada/live** no T-06. Revisão visual humana fica a critério do `/gsd:verify-work 3` após a phase.

---

## Reconciliation expectations

Ao fim da execução, `/gsd:reconcile-state 3` verifica:

- `apps/web` existe e builda; `_tokens.scss` é gerado (não escrito à mão).
- As 21 vars semânticas presentes nos dois temas; zero `#hex` fora do gerado.
- 4 componentes de estado em `shared/`; login conectado a `/v1/auth/login`; 3 shells + guarda.
- `authGuard` realmente protege rotas; token NÃO está em localStorage.
- Nenhum arquivo-fantasma; nenhuma feature fora de task (sem cadastro/dashboard/entrega).

---

## Rollback plan

Se este plano causar regressão:
- Revert dos commits `feat(phase-3/...)` (por wave).
- `apps/web` é app novo isolado — remover diretório não afeta `apps/api`.
- Sem migrations nem ações de ops (frontend-only, sem deploy nesta phase).

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | N/A justificado}
- Performance budget: {presente}
- Observability checklist: {N/A justificado}
- Error UX checklist: {presente}
- Integration contracts: {N/A justificado}
- Revision iteration: {1 | 2 | 3 | final}
