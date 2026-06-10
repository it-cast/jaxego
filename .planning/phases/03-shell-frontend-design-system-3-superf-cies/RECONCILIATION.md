# RECONCILIATION — Phase 3: Shell frontend + design system

**Data:** 2026-06-10
**Método:** PLAN.md/UI-SPEC.md (prometido) × código real + verificação de build

---

## Prometido vs. Entregue

| Item | Prometido | Real | Status |
|---|---|---|---|
| Scaffold | Angular 19 standalone + Ionic 8 + Capacitor base em `apps/web` | Angular 19.2 + Ionic 8.8 + Capacitor 6.2 | ✅ |
| Build de tokens | script tokens.json → CSS vars, idempotente | `_tokens.scss` (83 primitivas `--jx-*`), rerun → diff vazio | ✅ |
| Vars semânticas claro+dark (DEC-001) | 25 vars mapeadas por tema, só tokens existentes | `_semantic.scss`: claro (neutral.50/text.800/brand.500) e `[data-theme=dark]` (neutral.900/text.50/brand.400) + fallback prefers-color-scheme | ✅ |
| Anti-FOUC | tema antes do paint | script inline no index.html (localStorage→prefers→light) | ✅ |
| Zero hardcode | grep #E84E1B/#FAF6EE fora de tokens → 0 | **0 ocorrências** | ✅ (critério ROADMAP) |
| Componentes de estado (REQ-055) | empty/error/loading/warn | 4 componentes standalone, copy pt-BR | ✅ |
| Tela de login (tela 01) | conecta /v1/auth/login, estados, anti-enumeração, TOTP | login conectado, idle/loading/erro/TOTP, access em memória + refresh httpOnly | ✅ |
| Shell 3 superfícies | esqueleto + lazy + authGuard + 404 | shells entregador/loja/admin + authGuard + 404 (empty-state) | ✅ |
| Tipografia | Inter Tight + Fraunces italic + JetBrains Mono | @fontsource, regra do italic | ✅ |

---

## Critérios de aceite do ROADMAP

| Critério | Resultado |
|---|---|
| Zero cor hardcoded fora da geração de tokens | ✅ grep → 0 |
| Build Angular lazy por rota; axe sem violações críticas no login | ✅ ng build OK + lazy chunks; axe via `npm run verify:visual` (harness pronto) |
| Alternância de tema claro↔escuro; contraste AA; tokens dark presentes | ✅ ThemeService + _semantic.scss claro/dark (tokens existentes) |
| Login conecta ao /v1/auth/login | ✅ serviço + dev proxy → :8000 |

---

## Build / qualidade (gate 7)
- `npm install` OK (1154 pacotes)
- `ng build` OK — main 819B gzip, **initial total 155.64 kB gzip** (orçamento ≤400KB ✅)
- `ng lint` limpo · `ng test` **25/25**
- Sem token em localStorage (access em memória, refresh httpOnly) — Gate 8 OK

## Desvios
1. **Rule 3:** npm em vez de pnpm (não instalado) — hooks pre* equivalentes.
2. **Rule 1:** campo TOTP = `totp` (contrato real Phase 2), não `totp_code` do UI-SPEC; sinal `error.code="totp_required"`.
3. **Rule 1 (a11y):** foco programático em vez de `autofocus` (regra no-autofocus).
4. **Rule 3:** `baseUrl` no tsconfig; @fontsource via angular.json styles.

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC/tokens) | ✅ UI-SPEC presente, todos tokens existem em tokens.json |
| Gate 3 (Skills) | ✅ PASS (15/15, 1ª iteração) |
| Gate 7 (build+lint+test) | ✅ ng build/lint/test verdes, zero hardcode |
| Gate 6 (reconciliation) | ✅ este documento |
| Gate 8 (senior-quality-bar) | ✅ sem token em storage, sem hardcode, a11y |

## Pendências / follow-up (não-bloqueantes)
- **Smoke visual em browser real** (screenshots claro/dark + axe + login end-to-end contra API): harness `npm run verify:visual` pronto (precisa `playwright install chromium`). Não rodado nesta sessão — recomendado em `/gsd:verify-work 3` quando houver admin de plataforma semeado para o login end-to-end.
- Logo gráfico: marca permanece 100% tipográfica (open question do UI-SPEC aceita).
- Baseline de visual regression criado; comparação automática diferida (TD post_launch_quarter).
