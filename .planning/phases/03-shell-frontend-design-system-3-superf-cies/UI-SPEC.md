---
phase: 03-shell-frontend-design-system-3-superf-cies
title: Shell frontend + design system (3 superfícies)
status: draft
platform: web+mobile
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
---

# UI-SPEC — Phase 3: Shell frontend + design system (3 superfícies)

> Design contract. Gerado por `gsd-ui-researcher` em 2026-06-10. Aprovado por `gsd-ui-checker` em {date}.
> **BLOQUEIA** `plan-phase` se não existir (Gate 2 — Visual Contract).
> Plataforma: **web+mobile** (Angular 19 standalone + Ionic 8, 1 código / 3 superfícies).
> **Regra de ouro Gate 2:** todo valor visual é token. Nenhum `#hex` hardcoded fora do build `tokens.json → CSS vars`. Toda referência a token neste doc existe em `docs/identidade-visual/tokens.json` (ver §8).

---

## Fontes de verdade consultadas

- `docs/identidade-visual/tokens.json` — tokens **canônicos** (escalas brand/neutral 50–900, semantic, delivery_state, score_level, spacing, radius, font, shadow warm, motion). FONTE da verdade visual.
- `docs/identidade-visual/brand.md` — voz editorial-técnica, regra do Fraunces italic (1 palavra-chave por título), tom por contexto, formatos pt-BR.
- `design-system/MASTER.md` — catálogo de componentes extraído dos 26 wireframes.
- `projeto/wireframes/01-login.html` — contrato DOM da tela de login.
- `.planning/phases/03-.../03-CONTEXT.md` — decisões D-01..D-09, DEC-001 (dark mode no M1).
- `.planning/ROADMAP.md` — Phase 3 (flags: has_ui, has_api, mobile, dark_mode; skills da matriz UI).

### Skills aplicadas (matriz UI + DEC-001)

- `ux-advanced/design-tokens-system` — tokens primitivos (tokens.json) → camada semântica (CSS vars) → uso. Nunca consumir primitivo direto em componente.
- `ux-advanced/dark-mode-theming` — dois temas por troca de CSS vars semânticas no `:root`/`[data-theme]`; `prefers-color-scheme` + toggle persistido; anti-FOUC; preservar o "warm" no dark.
- `ui-ux-pro-max` — direção estética anti-AI-slop: editorial-técnica, persimmon queimado + cream warm, hierarquia tipográfica forte, mono em dados, NADA de gradientes genéricos / glassmorphism / laranja neon.
- `quality/accessibility-pro` — contraste AA nos dois temas, foco visível (shadow.focus), teclado, touch ≥44px, landmarks, live regions.
- `ux-advanced/empty-states-polish` — EmptyState com causa + ação, nunca "Lista vazia".
- `br/ux-copywriting-ptbr` — sentence case, CTA verbo+objeto ≤4 palavras sem ponto, erro = o que houve + o que fazer, anti-enumeração no login.
- `quality/error-ux-patterns` — ErrorState `role=alert`, WarnBanner não-bloqueante, mensagem acionável.
- `ux-advanced/responsive-breakpoint-strategy` — mobile-first (entregador), responsivo fluido (loja), desktop-first (admin) num só codebase.
- `product/component-library-governance` — componentes de estado canônicos compartilhados; baseline de visual regression criado nesta phase.
- `domain/ionic-patterns` + `domain/angular-material-patterns` — shell Ionic tabs (entregador), layouts Angular standalone por superfície.

---

## Telas / artefatos cobertos por esta fase

Esta phase entrega o **shell + design system**, não telas de negócio. Cobertos:

1. **Sistema de temas** (claro + dark) — CSS vars semânticas (§1)
2. **Tipografia** — escala + regra do italic + mono (§2)
3. **Componentes de estado canônicos** (REQ-055): `EmptyState`, `ErrorState`, `LoadingSkeleton`, `WarnBanner` (§3)
4. **Tela 01 — Login** (REQ-005, wireframe `01-login.html`) (§4)
5. **Shell esqueleto das 3 superfícies** + guarda de rota (§6)

**Fora de escopo (deferido):** cadastro loja/entregador (Phase 4/5), dashboards, listas, mapas, entrega, tracking. NÃO especificar aqui.

---

## 1. Sistema de temas (claro + dark — DEC-001)

### 1.1 Estratégia

- **Camada primitiva:** `tokens.json` gera CSS custom properties primitivas via build step (script Node → `_tokens.scss` / `:root` CSS vars), prefixadas `--jx-*`. Ex.: `--jx-brand-500: #E84E1B;`. **Geradas, não escritas à mão.**
- **Camada semântica:** este UI-SPEC define as vars semânticas abaixo. Cada uma aponta para uma var primitiva, **com valor diferente por tema**. Componentes consomem SÓ a camada semântica (`color: var(--surface)`), nunca a primitiva.
- **Troca de tema:** atributo `data-theme="light|dark"` no `<html>`. `:root` = claro (default). `:root[data-theme="dark"]` redefine as semânticas. Sem `data-theme` explícito, `@media (prefers-color-scheme: dark)` aplica o bloco dark.
- **Persistência:** toggle manual grava em `localStorage('jx-theme')`. Ordem de precedência: localStorage → `prefers-color-scheme` → claro.

### 1.2 Anti-FOUC (tema antes do paint)

Script **síncrono inline** no `<head>` do `index.html`, antes de qualquer CSS de componente e antes do bootstrap Angular:

```html
<script>
  (function () {
    var s = localStorage.getItem('jx-theme');
    var t = s || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>
```

Isso garante o atributo aplicado antes do primeiro paint (FOUC de tema é inaceitável — CONTEXT §specifics). O serviço Angular de tema lê/escreve o mesmo atributo + chave depois do bootstrap.

### 1.3 Mapeamento das CSS vars semânticas

**21 CSS vars semânticas**, cada uma mapeada para token existente em **cada tema**. Persimmon ajustado por luminância no dark (`brand.400` em vez de `brand.500`); warm preservado (sombras `rgba(24,20,16,…)` em ambos).

| CSS var semântica | Papel | CLARO → token | DARK → token |
|---|---|---|---|
| `--surface` | fundo base do app (cream warm) | `neutral.50` (#FAF6EE) | `neutral.900` (#0A0805) |
| `--surface-elevated` | cards, sheets, painéis acima do fundo | `neutral.100` (#F2EBE0) — ou branco `#fff` via wireframe; usamos `neutral.100` p/ ficar tokenizado | `neutral.800` (#181410) |
| `--surface-sunken` | áreas recuadas (inputs, wells, skeleton bg) | `neutral.200` (#E5DBCC) | `neutral.700` (#2D261F) |
| `--text` | texto primário (carvão amarronzado) | `neutral.800` (#181410) | `neutral.50` (#FAF6EE) |
| `--text-muted` | texto secundário / labels de apoio | `neutral.500` (#6B5F50) | `neutral.300` (#C8BAA5) |
| `--text-subtle` | texto terciário / placeholders / footer | `neutral.400` (#9D8E7A) | `neutral.400` (#9D8E7A) |
| `--border` | bordas de card/input em repouso | `neutral.200` (#E5DBCC) | `neutral.700` (#2D261F) |
| `--border-strong` | divisores fortes / borda de input focado base | `neutral.300` (#C8BAA5) | `neutral.600` (#4A4136) |
| `--brand` | ação primária, links de marca, italic editorial | `brand.500` (#E84E1B) | `brand.400` (#FB813D) |
| `--brand-hover` | hover/active do primário | `brand.600` (#C73E0F) | `brand.300` (#FFA56B) |
| `--brand-contrast` | texto sobre superfície `--brand` | `neutral.50` (#FAF6EE) | `neutral.900` (#0A0805) |
| `--brand-wash` | fundo de destaque suave (estimate box, selecionado) | `brand.50` (#FFF1E8) | `brand.900` (#421405) |
| `--brand-wash-border` | borda do wash | `brand.100` (#FFDEC1) | `brand.800` (#6F2308) |
| `--success` | sucesso (texto/ícone) | `semantic.success` (#1B998B) | `semantic.success` (#1B998B) |
| `--success-bg` | fundo de sucesso | `semantic.success_bg` (#D6F1ED) | `neutral.800` (#181410) c/ texto `--success` |
| `--warning` | aviso (texto/ícone WarnBanner) | `semantic.warning` (#E89B0E) | `semantic.warning` (#E89B0E) |
| `--warning-bg` | fundo de aviso | `semantic.warning_bg` (#FFF1D2) | `neutral.800` (#181410) c/ texto `--warning` |
| `--error` | erro (texto/ícone ErrorState) | `semantic.error` (#C71D1D) | `semantic.error` (#C71D1D) |
| `--error-bg` | fundo de erro | `semantic.error_bg` (#F9DCDC) | `neutral.800` (#181410) c/ texto `--error` |
| `--info` | links neutros / info | `semantic.info` (#0A66C2) | `semantic.info` (#0A66C2) |
| `--info-bg` | fundo info | `semantic.info_bg` (#DDEBFA) | `neutral.800` (#181410) c/ texto `--info` |

**Notas de contraste (validar no checker):**
- Dark: textos semânticos (`success`/`warning`/`error`/`info`) sobre `--surface-elevated` (#181410) — os hexes pastel `_bg` claros NÃO funcionam no dark, por isso o dark usa fundo neutro escuro + texto colorido vivo (padrão dark-mode-theming: superfície escura única, cor só no texto/borda). Borda esquerda 3px na cor semântica para reforçar.
- `--brand` no dark = `brand.400` (#FB813D) sobre `neutral.900` — luminância maior compensa o fundo escuro (anti "laranja apagado").
- Warm preservado: `--shadow-*` permanecem `rgba(24,20,16,…)` nos dois temas (ver §1.4), nunca cinza-azulado frio.

### 1.4 Sombras e foco (iguais nos dois temas — warm)

| CSS var | Mapeamento token | Observação |
|---|---|---|
| `--shadow-sm` | `shadow.sm` | warm `rgba(24,20,16,…)` — mantido no dark |
| `--shadow-md` | `shadow.md` | cards/sheets |
| `--shadow-lg` | `shadow.lg` | overlays/modais |
| `--focus-ring` | `shadow.focus` | `0 0 0 3px rgba(232,78,27,.28)` — anel de foco persimmon, ambos os temas |

No dark, sombras `rgba(24,20,16,…)` somem visualmente sobre fundo escuro; a elevação é comunicada por `--surface-elevated` mais clara que `--surface`. Foco persimmon vale para os dois (contraste suficiente sobre claro e escuro).

---

## 2. Tipografia

Tudo via tokens `font.*`. Nenhum `font-family` inline em template (consumir `var(--jx-font-display)` etc.).

### 2.1 Famílias (de `font.family`)

| Uso | Token | Quando |
|---|---|---|
| Display / body / UI | `font.family.display` (`'Inter Tight'…`) | tudo: títulos, corpo, botões, labels, tabelas |
| Acento editorial | `font.family.serif_accent` (`'Fraunces'…`) | **só** 1 palavra-chave por título/hero, em italic, cor `--brand` |
| Dados | `font.family.mono` (`'JetBrains Mono'…`) | IDs, valores R$, scores, timestamps, placas, request_id |

### 2.2 Regra do italic (brand.md — inviolável)

- Fraunces **italic** em **UMA** palavra-chave por título/hero, cor `--brand`, weight `font.weight.medium` (500).
- Ex. login (do wireframe): `Jaxegô. Chegou <em>rapidinho.</em>` — `rapidinho.` em Fraunces italic brand.
- **NUNCA** em: botões, labels, tabelas, mensagens de erro, dados em mono, copy de estado.

### 2.3 Escala (de `font.size` — usar 4 tamanhos centrais por superfície)

| Papel | Token size | px | Peso (token) |
|---|---|---|---|
| Hero / H1 | `font.size.2xl` | 28 | `weight.semibold` (600), letter-spacing -.02em |
| Título de seção / H2 | `font.size.xl` | 22 | `weight.semibold` (600) |
| Subtítulo / H3 | `font.size.lg` | 18 | `weight.medium` (500) |
| Corpo / UI base | `font.size.base` | 14 | `weight.regular` (400) |
| Apoio / label | `font.size.sm` | 13 | `weight.semibold` (600) |
| Caption / footer / overline | `font.size.xs` | 12 | `weight.regular` (400) / overline 600 uppercase |

- **Money/score display:** `font.size.2xl` (28) ou `font.size.3xl` (36) em mono, `weight.extrabold` (800), -.02em (padrão MASTER §2).
- **Line-height:** corpo 1.5; headings 1.2.
- **Label de seção (overline):** `font.size.2xs` (11) ou `xs` (12), uppercase, letter-spacing .08em, `weight.semibold`, cor `--text-muted`.

### 2.4 Pesos disponíveis

`font.weight.regular` 400 · `medium` 500 · `semibold` 600 · `bold` 700 · `extrabold` 800 (só money/score display). Uso UI predominante: 400 (corpo) + 600 (ações/labels).

---

## 3. Espaçamento, raio, motion

- **Spacing** (de `spacing`): 4/8/12/16/24/32/48/64/96. Consumir `var(--jx-space-4)` (=16px) etc. Nunca `padding: 16px`.
- **Radius** (de `radius`): `sm` 4 · `md` 6 (inputs) · `lg` 10 (cards) · `xl` 16 (sheets) · `full` (pills/toggles/avatar).
- **Motion** (de `motion`): `fast` 140ms · `normal` 220ms · `slow` 380ms · easing `easing_out` `cubic-bezier(0.16,1,0.3,1)`.
  - Botão press: scale .97, `fast`. Sheet/overlay: slide-up `normal`. Skeleton pulse: 1.2s loop (do wireframe). **Respeitar `prefers-reduced-motion`** (desliga transform/loop).
  - Anti-pattern: nunca animar além de `transform`/`opacity`; nada >500ms em ação crítica.

---

## 4. Componentes de estado canônicos (REQ-055)

Componentes Angular standalone compartilhados (`shared/`), presentes em todas as telas dali em diante. Copy pt-BR (`br/ux-copywriting-ptbr`). Tokens semânticos só (§1).

### 4.1 `jx-empty-state`

- **Quando:** API/lista retorna 0 itens (estado legítimo, não erro).
- **Anatomia:** ícone/ilustração leve (Ionicon ou glyph, `--text-subtle`) → título `font.size.lg`/`--text` → frase de causa `font.size.base`/`--text-muted` → CTA primário (botão `--brand`, opcional).
- **Tokens:** fundo `--surface`; ícone `--text-subtle`; CTA `--brand`/`--brand-contrast`; padding `--jx-space-6` (32).
- **Copy (regra brand: causa + ação, nunca "Lista vazia"):**
  - "Nenhuma entrega ainda. Crie a primeira no botão acima." (exemplo de brand.md)
  - "Nada por aqui ainda." + CTA "Criar agora" (genérico parametrizável).
- **A11y:** `role="status"`, foco move para o título ao montar se substituir conteúdo carregado.

### 4.2 `jx-error-state`

- **Quando:** 4xx/5xx da API ou falha de carregamento.
- **Anatomia:** banner/bloco fundo `--error-bg`, texto `--error`, borda esquerda 3px `--error`; mensagem (o que houve) + ação (o que fazer / retry).
- **Tokens:** `--error`, `--error-bg`; radius `md`; padding `--jx-space-3` (12); ícone alerta `--error`.
- **Copy (o que houve + o que fazer — nunca "Algo deu errado"):**
  - "Não conseguimos carregar as entregas. Tente de novo em alguns segundos." + botão "Tentar de novo".
  - Erro de servidor: "Tivemos um problema aqui. Já estamos vendo — tente em instantes."
- **A11y:** `role="alert"` (anuncia imediato); botão retry com label claro; touch ≥44px.

### 4.3 `jx-loading-skeleton`

- **Quando:** requisição em curso ao montar. **Skeleton do layout real, não spinner** (REQ-055 + MASTER).
- **Anatomia:** blocos com fundo `--surface-sunken`, radius `md`/`lg` conforme o conteúdo que substituem, animação pulse (`@keyframes` opacity 1→.5→1, 1.2s `infinite`, do wireframe).
- **Tokens:** fundo `--surface-sunken`; radius conforme alvo; motion pulse 1.2s.
- **A11y:** `aria-hidden="true"` (não anuncia); container pai com `aria-busy="true"`; `prefers-reduced-motion` → sem pulse (bloco estático).
- **Composição:** primitivos `skeleton-line` (altura `font.size.base`), `skeleton-block` (altura configurável), `skeleton-circle` (avatar). Ionic skeleton aceito no app entregador; custom nos demais (Discretion D — decidido: custom token-driven para consistência cross-superfície).

### 4.4 `jx-warn-banner`

- **Quando:** aviso **não-bloqueante** (ação degradada, validação pendente, conexão instável). Difere de error: usuário pode prosseguir.
- **Anatomia:** banner inline fundo `--warning-bg`, texto `--warning`, borda esquerda 3px `--warning`, ícone aviso; dispensável (`x`) opcional.
- **Tokens:** `--warning`, `--warning-bg`; radius `md`; padding `--jx-space-3`.
- **Copy (≤12 palavras na 1ª frase, brand.md):**
  - "Sua loja está em validação simples. Algumas funções ficam liberadas após a completa."
  - "Conexão instável. Mostrando dados salvos." (offline-ish, não-bloqueante)
- **A11y:** `role="status"` (não interrompe); botão dispensar com `aria-label="Dispensar aviso"`, touch ≥44px.

**Estados mínimos por superfície:** toda tela futura cobre os 5 estados (loading / empty / success / error / offline-mobile) reusando estes componentes — contrato validado por `gsd-tools wireframe-contract`.

---

## 5. Tela 01 — Login (REQ-005, wireframe `01-login.html`)

### 5.1 Layout

- **Container:** `<main>` centralizado, `max-width` ~400px (mobile-first; funciona em todas as superfícies). Margem topo `--jx-space-7` (48), padding lateral `--jx-space-4` (16).
- **Header:** `<h1>` "Jaxegô. Chegou *rapidinho.*" — `rapidinho.` em Fraunces italic `--brand`, weight 500. `font.size.2xl` (28), -.02em.
- **Form:** vertical stack, gap `--jx-space-4`.
- **Footer:** "jaxego.com.br · Grupo Itcast", `font.size.xs`, `--text-subtle`, centralizado, topo `--jx-space-6`.

### 5.2 Campos

| Campo | Tipo | Atributos | Tokens |
|---|---|---|---|
| E-mail | `email` | `required`, `inputmode="email"`, `autocomplete="email"`, `enterkeyhint="next"`, placeholder "voce@exemplo.com.br" | borda `--border-strong`, focus `--focus-ring`, fundo `--surface-elevated`, texto `--text` |
| Senha | `password` | `required`, `minlength="10"`, `autocomplete="current-password"`, `enterkeyhint` "next" (se TOTP possível) ou "send", toggle mostrar/ocultar (`aria-label`) | idem |
| Código TOTP **(condicional)** | `text` | aparece SÓ se backend responder exigência de 2FA; `inputmode="numeric"`, `autocomplete="one-time-code"`, `maxlength="6"`, `enterkeyhint="send"`, fonte mono | idem; dígitos em `font.family.mono` |
| Botão Entrar | submit | full-width, padding `--jx-space-4`, `--brand`/`--brand-contrast`, radius `md`/`lg`, weight 600, touch ≥44px | press scale .97 `fast` |

- **Links:** "Esqueci a senha" / "Criar conta" (linha, `space-between`), cor `--info`, `font.size.sm`. Bloco inferior (borda topo `--border`): "Cadastrar minha loja →" / "Quero entregar →".

### 5.3 Estados

| Estado | Quando | Aparência | A11y |
|---|---|---|---|
| **Idle** | inicial | form completo, botão habilitado | foco inicial no campo e-mail |
| **Loading** | submit em curso | botão desabilitado + `jx-loading-skeleton` (bloco 44px, do wireframe), `aria-busy` | sem duplo submit |
| **Erro (anti-enumeração)** | 401/credencial inválida | `jx-error-state` inline, fundo `--error-bg`, texto `--error` | `role="alert"`, foco move ao alerta |
| **TOTP requerido** | backend sinaliza 2FA | revela campo Código TOTP, foca nele, copy de instrução | `aria-live="polite"` ao revelar |
| **Sucesso** | 200 + token | sem toast festivo; redireciona ao shell da superfície do usuário | — |

### 5.4 Copy pt-BR (anti-enumeração — RN-011/ADR-005, brand.md)

- Erro credencial (NUNCA revelar se e-mail existe): **"E-mail ou senha incorretos. Tente de novo ou recupere a senha."** (texto do wireframe — backend já manda `error.message` anti-enumeração; frontend exibe `message`).
- TOTP: **"Digite o código do seu app autenticador."** (instrução) — campo label "Código de verificação".
- Erro de rede: **"Sem conexão com o servidor. Verifique sua internet e tente de novo."**
- Botão: **"Entrar"** (verbo, sem ponto). Loading: botão mantém "Entrar" desabilitado (sem trocar para "Entrando…" para evitar layout shift — skeleton comunica).

### 5.5 Integração `/v1/auth/login` (D-07/D-08)

- POST `/v1/auth/login` `{ email, password, totp_code? }`. Envelope erro `{ error: { code, message, request_id } }` → exibir `message` (já anti-enumeração).
- Resposta 200: **access token em memória** (signal/serviço), **refresh em cookie httpOnly** (web). Sem token em localStorage.
- Sinal de 2FA: backend responde código/estado específico (ex. `error.code = totp_required` ou flag) → revela campo TOTP e reenvia com `totp_code`.
- Dev: proxy Angular para API porta 8000 (CORS).
- `request_id` do erro logado em observabilidade (não exibido ao usuário, salvo fallback técnico).

---

## 6. Shell das 3 superfícies (esqueleto + guarda de rota — D-09)

Um app Angular standalone, layouts/rotas por superfície, **lazy por rota** (DRV-004). Nesta phase só o **esqueleto navegável + guarda**, sem telas de negócio.

### 6.1 Estrutura

| Superfície | Layout | Esqueleto desta phase | Tokens-chave |
|---|---|---|---|
| **Entregador** (mobile-first) | Ionic `ion-tabs`, tabbar fixa inferior (Início / Entregas / Ganhos / Perfil), conteúdo ≤420px | shell `ion-tabs` + 4 abas placeholder com `jx-empty-state`; `aria-current="page"` na aba ativa | `--surface`, tabbar `--surface-elevated`, ativo `--brand`, safe-area insets |
| **Loja** (web responsivo) | container centrado 620–860px, topbar simples + área de conteúdo | layout web com topbar + slot de rota (placeholder EmptyState) | `--surface`, topbar `--surface-elevated`, `--border` |
| **Admin** (desktop-first) | sidebar fixa esquerda + área densa de conteúdo | layout sidebar colapsável + slot (placeholder) | `--surface-sunken` (sidebar) / `--surface` (conteúdo), mono em valores |

- **Theme toggle:** disponível no shell de cada superfície (perfil/topbar/sidebar) — alterna `data-theme`, persiste `localStorage('jx-theme')`. `aria-pressed`, label "Tema escuro".
- **Pastas (Discretion):** `core/` (guards, auth service, theme service, http), `shared/` (componentes de estado, tokens, design primitives), `features/` (placeholder por superfície), `layouts/` (3 shells).

### 6.2 Guarda de rota (D-08)

- `authGuard` (functional guard, Angular 19): se não autenticado (sem access token em memória / refresh falha) → redireciona `/entrar`.
- Rotas de superfície (`/entregador/**`, `/loja/**`, `/admin/**`) protegidas. `/entrar` pública.
- Pós-login: redireciona para a superfície conforme tipo de usuário retornado pelo backend.
- Sem rota correspondente → 404 placeholder usando `jx-empty-state` ("Página não encontrada." + CTA "Voltar ao início").

---

## 7. Acessibilidade (mínimo obrigatório — accessibility-pro, D-05)

- **Contraste AA nos DOIS temas:** ≥4.5:1 texto normal, ≥3:1 texto grande/UI. Validar `--text`/`--surface` e `--brand-contrast`/`--brand` em claro e dark. (Mapas de §1.3 desenhados para isso; checker valida com axe + contraste.)
- **Foco visível:** `--focus-ring` (`shadow.focus`) em todo interativo. NUNCA `outline:none` sem substituto.
- **Touch targets ≥44×44px** no mobile (botão login, abas, toggle, dispensar warn) — `accessibility-pro` + iOS HIG.
- **Labels:** todo input com `<label for>`; botões icon-only com `aria-label`.
- **Live regions:** `jx-error-state` `role="alert"`; `jx-empty-state`/`jx-warn-banner` `role="status"`; skeleton `aria-hidden` + container `aria-busy`.
- **Landmarks:** `<main>`, `<nav>` (tabbar/sidebar), `aria-current="page"` na navegação ativa.
- **Teclado:** ordem de tabulação lógica; Enter submete login; `prefers-reduced-motion` respeitado (skeleton/transições).
- **`lang="pt-BR"`** no documento (já no wireframe — manter).
- **CI:** `axe-core` na tela de login, zero violações críticas (verificação do ROADMAP).

---

## 8. Tabela de tokens citados (Gate 2 — todos existem em `tokens.json`)

Cada token referenciado neste UI-SPEC, com caminho em `docs/identidade-visual/tokens.json`. **Confirmado: 100% existem (zero inventados).**

| Token (caminho em tokens.json) | Valor | Existe? |
|---|---|---|
| `color.brand.50` | #FFF1E8 | ✅ |
| `color.brand.100` | #FFDEC1 | ✅ |
| `color.brand.300` | #FFA56B | ✅ |
| `color.brand.400` | #FB813D | ✅ |
| `color.brand.500` | #E84E1B | ✅ |
| `color.brand.600` | #C73E0F | ✅ |
| `color.brand.800` | #6F2308 | ✅ |
| `color.brand.900` | #421405 | ✅ |
| `color.neutral.50` | #FAF6EE | ✅ |
| `color.neutral.100` | #F2EBE0 | ✅ |
| `color.neutral.200` | #E5DBCC | ✅ |
| `color.neutral.300` | #C8BAA5 | ✅ |
| `color.neutral.400` | #9D8E7A | ✅ |
| `color.neutral.500` | #6B5F50 | ✅ |
| `color.neutral.600` | #4A4136 | ✅ |
| `color.neutral.700` | #2D261F | ✅ |
| `color.neutral.800` | #181410 | ✅ |
| `color.neutral.900` | #0A0805 | ✅ |
| `color.semantic.success` | #1B998B | ✅ |
| `color.semantic.success_bg` | #D6F1ED | ✅ |
| `color.semantic.warning` | #E89B0E | ✅ |
| `color.semantic.warning_bg` | #FFF1D2 | ✅ |
| `color.semantic.error` | #C71D1D | ✅ |
| `color.semantic.error_bg` | #F9DCDC | ✅ |
| `color.semantic.info` | #0A66C2 | ✅ |
| `color.semantic.info_bg` | #DDEBFA | ✅ |
| `spacing.1` … `spacing.9` | 4 … 96px | ✅ |
| `radius.sm` / `md` / `lg` / `xl` / `full` | 4/6/10/16/9999px | ✅ |
| `font.family.display` | Inter Tight… | ✅ |
| `font.family.serif_accent` | Fraunces… | ✅ |
| `font.family.body` | Inter Tight… | ✅ |
| `font.family.mono` | JetBrains Mono… | ✅ |
| `font.size.2xs`…`5xl` (usados: 2xs/xs/sm/base/lg/xl/2xl/3xl) | 11…36px | ✅ |
| `font.weight.regular`…`extrabold` | 400…800 | ✅ |
| `shadow.sm` / `md` / `lg` / `focus` | warm rgba(24,20,16,…) / focus persimmon | ✅ |
| `motion.fast` / `normal` / `slow` / `easing_out` | 140/220/380ms / cubic-bezier | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Gate 2 satisfeito — toda var semântica deriva de escala existente; o dark mode reaproveita `neutral.600–900` e `brand.300/400/800/900` sem inventar hex.

---

## 9. Visual regression (baseline criado nesta phase)

Componentes novos compartilhados que recebem story/baseline (`product/visual-regression-testing` — baseline, não comparação ainda):

- [ ] `jx-empty-state` — stories: default, com-cta, sem-cta · temas claro+dark
- [ ] `jx-error-state` — stories: padrão, com-retry · claro+dark
- [ ] `jx-loading-skeleton` — stories: line, block, circle, composição-card · claro+dark
- [ ] `jx-warn-banner` — stories: padrão, dispensável · claro+dark
- [ ] `login` (tela 01) — stories: idle, loading, erro, totp · claro+dark

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`. Baseline capturado ao fim da phase.

---

## 10. Open questions para o humano

- [ ] **Logo:** MASTER §4 marca [GAP] — marca é 100% tipográfica ("Jaxegô. Chegou *rapidinho.*") ou existe logo gráfico? **Recomendação:** seguir 100% tipográfica nesta phase (login usa a assinatura), confirmar antes de phases com header de marca.
- [ ] **`--surface-elevated` claro:** wireframe usa `#fff` puro em cards; mapeei para `neutral.100` (#F2EBE0) para ficar 100% tokenizado e warm. **Recomendação:** manter `neutral.100` (mais coeso com cream warm que branco puro); se humano quiser branco, adicionar token `neutral.0: #FFFFFF` em tokens.json (decisão consciente, não inventar em CSS).

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§8)
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 3` — o planner recebe este UI-SPEC como contexto e contrato de design.
