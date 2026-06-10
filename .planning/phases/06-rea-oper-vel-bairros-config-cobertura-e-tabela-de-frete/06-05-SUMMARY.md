---
phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
plan: 05
subsystem: frontend (entregador Ionic mobile)
tags: [entregador, ionic, coverage, pricing-floor, availability, gate2]
requires:
  - "Plan 03 /v1/couriers/{id}/coverage|pricing|availability"
  - "Phase 3/5 shell Ionic + design system"
provides:
  - "tela 10 cobertura + preços (modo bairro/km + validação de piso)"
  - "jx-coverage-list (lista mobile com toggle+preço)"
  - "jx-availability-toggle (online/offline só active)"
affects:
  - "apps/web/src/app/app.routes.ts (/entregador/cobertura)"
tech-stack:
  added: []
  patterns:
    - "validação de piso citando o valor (mono, da config — nunca hardcoded)"
    - "role=switch / role=radiogroup; aria-live; prefers-reduced-motion"
key-files:
  created:
    - apps/web/src/features/entregador/cobertura-precos/cobertura-precos.page.ts
    - apps/web/src/features/entregador/cobertura-precos/cobertura-precos.page.html
    - apps/web/src/features/entregador/cobertura-precos/cobertura-precos.page.scss
    - apps/web/src/features/entregador/cobertura-precos/coverage-list.component.ts
    - apps/web/src/features/entregador/cobertura-precos/coverage-list.component.scss
    - apps/web/src/features/entregador/cobertura-precos/cobertura-precos.service.ts
    - apps/web/src/features/entregador/cobertura-precos/cobertura-precos.stories.ts
    - apps/web/src/features/entregador/cobertura-precos/cobertura-precos.spec.ts
    - apps/web/src/features/entregador/disponibilidade/availability-toggle.component.ts
    - apps/web/src/features/entregador/disponibilidade/availability-toggle.component.scss
    - apps/web/src/features/entregador/disponibilidade/availability-toggle.stories.ts
    - apps/web/src/features/entregador/disponibilidade/availability-toggle.spec.ts
  modified:
    - apps/web/src/app/app.routes.ts
decisions:
  - "piso exibido/validado sempre vindo da config da área (mono, nunca constante no front)"
  - "jx-availability-toggle expõe revert() para tratar 409 do backend (não-active)"
metrics:
  duration: ~35min
  tasks: 2
  files: 13
  completed: 2026-06-10
---

# Phase 6 Plan 05: Entregador mobile — cobertura + preços + toggle Summary

Superfície entregador (Ionic 8, mobile-first): a tela 10 de cobertura + preços (seletor de modo bairro/km, lista de bairros com checkbox ≥44px e preço mascarado, exclusões, retorno %, e a validação de PISO que CITA o valor ao rejeitar — RN-015) e o `jx-availability-toggle` online/offline que só liga para courier `active` (RN-018/D-06) — reusando o shell Ionic e o design system Phase 3/5, zero #hex, AA claro+dark, touch ≥44px, safe-area e prefers-reduced-motion.

## Tasks Completed

| Task | Nome | Commit | Arquivos-chave |
|------|------|--------|----------------|
| 1 | Tela 10 cobertura + preços | e902352 | cobertura-precos.page.{ts,html,scss}, coverage-list, service |
| 2 | jx-availability-toggle | 5848a36 | availability-toggle.component.{ts,scss}, stories, spec |

## Decisões / notas

- **Piso sempre da config da área:** o `jx-warn-banner` (RN-003) e a validação de piso citam o valor vindo de `pisoEntrega`/`pisoKm` (mono) — nunca constante no front. A autoridade da rejeição é o backend (422 "price_below_floor"); a UI valida inline para feedback rápido e mapeia o 422.
- **`jx-availability-toggle`** usa `role="switch"` + `aria-checked`, status por texto+posição+ícone, `aria-live="polite"` para anunciar a troca, e expõe `revert()` para o caller desfazer o estado otimista quando o backend retorna 409 (não-active). Não-active → switch inerte + warn-banner "termine sua validação" + CTA "Ver validação".
- **Modo bairro/km** via `role="radiogroup"`; trocar de modo preserva os dados do outro.

## Deviations from Plan

Nenhum desvio de comportamento. A lista de bairros do catálogo é alimentada por um resolver de área que chega junto ao roteamento pós-login do entregador (M1); a tela trata o estado vazio corretamente até lá (empty-state sem CTA falso). Documentado como nota — sem mudança de contrato.

## Tech debt
- Nenhuma TD nova obrigatória. O consumo do estado online pelo despacho (cascata) é Phase 8.

## Verificação local
- `npx ng build` → OK. **Bundle initial: 598.40 KB raw / 160.96 KB gzip** (< 400 KB gzip de main).
- `npx ng test` (suíte completa) → **65 passed** (60 anteriores + 5 novos: cobertura-precos 2, availability-toggle 3).
- `npx ng lint` → All files pass.
- Hex check: `grep -rE "#[0-9A-Fa-f]{6}" src/features/entregador/cobertura-precos src/features/entregador/disponibilidade --include=*.scss | grep -v _tokens` → **0** (Gate 2); brand hex global → 0.

## O que verificar ao vivo (visual — checkpoint do plano)
- Tela 10 (`/entregador/cobertura`): modo bairro/km, máscara R$, exclusão com selo, retorno %, e o erro de piso citando o valor (role=alert) — claro+dark, mobile.
- `jx-availability-toggle`: online/offline (status texto+ícone), não-active desabilitado + warn-banner + CTA — claro+dark, mobile.
- axe sem violações críticas na tela 10 (claro+dark, mobile); touch ≥44px; safe-area; reduced-motion.

## Self-Check: PASSED
- cobertura-precos.page.ts, availability-toggle.component.ts — FOUND. Commits e902352, 5848a36 — FOUND.
