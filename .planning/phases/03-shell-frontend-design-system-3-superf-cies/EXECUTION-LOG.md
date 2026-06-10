# EXECUTION-LOG — Phase 3: Shell frontend + design system (3 superfícies)

> Executado por `gsd-executor` em 2026-06-10. App novo em `apps/web/`.
> Stack: Angular 19.2 standalone + signals + OnPush + control flow + lazy routes
> (DRV-004), Ionic 8.8, Capacitor 6.2 (base, sem build nativo — Phase 14),
> SCSS + CSS vars geradas de `tokens.json`.

## Resumo

6/6 tasks (T-01..T-06) executadas na ordem das waves, 1 commit atômico por task.
Todos os gates locais (build, lint, testes, zero-hardcode, sem token em
localStorage) verdes.

## Tasks e commits

| Wave | Task | Commit | Descrição |
|------|------|--------|-----------|
| 1 | T-01 | `2b75f89` | Scaffold `apps/web` (Angular 19 + Ionic 8 + Capacitor 6) |
| 2 | T-02 | `ca9c22a` | Build `tokens.json → _tokens.scss` + 21 vars semânticas claro/dark |
| 3 | T-03 | `86e140a` | Sistema de tema (ThemeService signal + toggle + anti-FOUC) + tipografia |
| 4 | T-04 | `aa675d4` | Componentes de estado (REQ-055): empty/error/loading/warn |
| 5 | T-05 | `8a7a2ed` | Login conectado a `/v1/auth/login` (idle/loading/erro/totp) |
| 6 | T-06 | `504d84e` | Shell 3 superfícies (lazy + authGuard + 404) + harness visual baseline |

## Resultado das verificações (gate 7)

- **`npm install`** (apps/web): OK — 1154 pacotes, sem erros (warns de deprecação
  transitivos apenas).
- **`ng build`** (production): OK. `main` = 819 B gzip; **initial total = 155.64 kB
  gzip** (orçamento `main` ≤ 400KB e initial ≤ 800KB ambos atendidos).
  Lazy chunk por superfície gerado: `login-page`, `entregador-shell-component`,
  `loja-shell-component`, `admin-shell-component`, `not-found-page`, `inicio-page`.
- **Zero hardcode:** `grep -rE "#E84E1B|#FAF6EE" apps/web/src --include="*.scss" |
  grep -v _tokens.scss` → **0 ocorrências**.
- **`_tokens.scss` idempotente:** rerun do `build-tokens.mjs` → `git diff` vazio
  (83 primitivas `--jx-*`).
- **`ng lint`:** **All files pass linting.**
- **`ng test`** (Karma + ChromeHeadlessCI): **25/25 SUCCESS** (theme service 5,
  state components 13, auth service 5, login page 5, auth guard 2 — somando
  via specs; total reportado 25).
- **Sem token em localStorage:** grep de `localStorage.(set|get)Item` com
  token/access/refresh → **0** (access em memória; refresh em cookie httpOnly).

## Desvios (deviation rules)

- **[Rule 1 — Contrato] Campo TOTP é `totp`, não `totp_code`.** O UI-SPEC §5.5
  diz `totp_code`, mas o contrato real da Phase 2 (`apps/api/app/auth/schemas.py
  LoginBody`) usa `totp`. Seguido o contrato real do backend. Sinal de 2FA =
  `error.code = "totp_required"` (status 401), confirmado em `service.py`.
- **[Rule 3 — Tooling] npm em vez de pnpm.** O PLAN cita `pnpm`; pnpm não está
  instalado no ambiente (Windows, Node 24.15.0, npm 11.12.1). Usado npm; scripts
  e hooks (`prebuild`/`prestart`/`pretest` → `tokens:build`) equivalentes.
- **[Rule 1 — a11y] `autofocus` → foco programático.** Regra
  `@angular-eslint/template/no-autofocus` bloqueia o atributo `autofocus`. Foco
  inicial no e-mail movido para `ngAfterViewInit` via `viewChild` (melhor prática,
  mantém o requisito de foco do UI-SPEC §5.3).
- **[Rule 3 — build] `baseUrl` adicionado ao tsconfig** para habilitar os path
  aliases (`@core/*` etc.); sem ele o Angular compiler falhava.
- **[Rule 3 — fonts] @fontsource via `angular.json styles`** em vez de `@use` no
  SCSS — `@use` de CSS com nome numérico (`400.css`) gera namespace Sass inválido
  e quebra a resolução de `url()`. Movido para o array `styles` (resolução de
  asset correta, `font-display: swap`).

## Dívidas técnicas geradas

- **TD candidato:** Visual regression é **baseline-only** (harness
  `scripts/visual-baseline.mjs` com Playwright + axe pronto, mas sem comparação
  automática nem Playwright instalado por padrão). `urgency_class:
  post_launch_quarter` se a comparação não entrar até a próxima phase de UI.

## Decisões conscientes (open questions do UI-SPEC §10)

- **Logo 100% tipográfica** ("Jaxegô. Chegou *rapidinho.*") — sem logo gráfico
  no shell. Confirmar com humano antes de phases com header de marca.
- **`--surface-elevated` claro = `neutral.100`** (#F2EBE0), não `#fff`, para
  manter 100% tokenizado e warm. Se branco puro for desejado, adicionar
  `neutral.0` em `tokens.json` (decisão consciente, fora desta phase).

## Como verificar ao vivo (orquestrador)

1. **Subir a API** (Phase 2) na porta 8000 (o proxy do Angular roteia `/v1` → :8000).
2. **Servir o app:** `cd apps/web && npm start` (usa `proxy.conf.json`). Abrir
   http://localhost:4200 → redireciona para `/entrar`.
3. **Tema claro/dark:** no `/entrar` não há toggle (login é minimal); use o toggle
   no shell (ex.: `/entregador/perfil`, topbar da loja, sidebar do admin) OU
   `localStorage.setItem('jx-theme','dark')` + reload — **não deve haver flash**
   de tema claro (anti-FOUC). Conferir nos dois temas: persimmon vivo no dark
   (brand.400), warm preservado, contraste AA.
4. **Login contra a API:** credencial válida → redireciona; credencial inválida →
   "E-mail ou senha incorretos…" (anti-enumeração, `role=alert`); usuário com 2FA
   → revela campo "Código de verificação" e reenvia com `totp`.
5. **Guarda de rota:** acessar `/entregador` sem login → redireciona para `/entrar`.
6. **404:** acessar `/qualquer-coisa` → `jx-empty-state` "Página não encontrada."
7. **Baseline visual + axe (opcional):** `npm i -D playwright @axe-core/playwright
   && npx playwright install chromium`, com o app servindo: `npm run verify:visual`
   → captura `apps/web/visual-baseline/{screen}-{theme}.png` e falha em qualquer
   violação crítica de a11y.

## Duração

Início: 2026-06-10T15:16:30Z · Fim: 2026-06-10T15:46:07Z (~30 min de execução).
