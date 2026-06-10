---
phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
plan: 04
subsystem: frontend (admin web — config + catálogo)
tags: [admin, data-table, area-config, neighborhoods, money-mask, gate2]
requires:
  - "Plan 01 /v1/areas/{id} (AreaConfig)"
  - "Plan 02 /v1/neighborhoods (CRUD)"
  - "Phase 3 design system + estados; Phase 5 padrão de painel admin"
provides:
  - "jx-data-table (primitivo governado)"
  - "tela 21A config da área (máscara monetária + confirmação sensível)"
  - "tela 21B catálogo de bairros CRUD"
  - "shared/util/money (máscara pt-BR)"
affects:
  - "apps/web/src/app/app.routes.ts (/admin/config, /admin/bairros)"
tech-stack:
  added: []
  patterns:
    - "jx-data-table com células projetadas (ng-template #row) + jx-neighborhood-row display:contents"
    - "máscara monetária pt-BR (nunca type=number cru para dinheiro)"
key-files:
  created:
    - apps/web/src/shared/components/data-table/data-table.component.ts
    - apps/web/src/shared/components/data-table/data-table.component.scss
    - apps/web/src/shared/components/data-table/data-table.stories.ts
    - apps/web/src/shared/components/data-table/data-table.spec.ts
    - apps/web/src/shared/util/money.ts
    - apps/web/src/features/admin/area-config/area-config.page.ts
    - apps/web/src/features/admin/area-config/area-config.page.html
    - apps/web/src/features/admin/area-config/area-config.page.scss
    - apps/web/src/features/admin/area-config/area-config.service.ts
    - apps/web/src/features/admin/area-config/area-config.stories.ts
    - apps/web/src/features/admin/area-config/area-config.spec.ts
    - apps/web/src/features/admin/neighborhoods/neighborhoods.page.ts
    - apps/web/src/features/admin/neighborhoods/neighborhoods.page.html
    - apps/web/src/features/admin/neighborhoods/neighborhoods.page.scss
    - apps/web/src/features/admin/neighborhoods/neighborhood-row.component.ts
    - apps/web/src/features/admin/neighborhoods/neighborhood-row.component.scss
    - apps/web/src/features/admin/neighborhoods/neighborhoods.service.ts
    - apps/web/src/features/admin/neighborhoods/neighborhoods.stories.ts
    - apps/web/src/features/admin/neighborhoods/neighborhoods.spec.ts
  modified:
    - apps/web/src/app/app.routes.ts
decisions:
  - "jx-data-table com content projection (ng-template #row); jx-neighborhood-row display:contents preserva semântica da tabela"
  - "máscara monetária própria em shared/util/money (parse/format pt-BR) — não type=number"
metrics:
  duration: ~45min
  tasks: 3
  files: 20
  completed: 2026-06-10
---

# Phase 6 Plan 04: Admin web — config + catálogo Summary

Superfície admin de área (web desktop-first): o primitivo governado `jx-data-table` (header sticky + aria-sort + 4 estados embutidos), a tela 21A de config da área (4 fieldsets, máscara monetária pt-BR, ranges validados no blur, confirmação before→after antes do PATCH auditado) e a tela 21B de catálogo de bairros (CRUD sobre `jx-data-table`, polígono GeoJSON opcional, remoção bloqueada citando o bairro) — tudo reusando o design system Phase 3/4/5, zero #hex, AA claro+dark.

## Tasks Completed

| Task | Nome | Commit | Arquivos-chave |
|------|------|--------|----------------|
| 1 | jx-data-table primitivo | b69912b | data-table.component.{ts,scss}, stories, spec |
| 2 | Tela 21A config da área | 35b1d61 | area-config.page.{ts,html,scss}, money.ts, service |
| 3 | Tela 21B catálogo de bairros | ad0967f | neighborhoods.page.{ts,html,scss}, neighborhood-row, service |

## Decisões / notas

- **jx-data-table com content projection:** o consumidor passa `<ng-template #row let-item>` que renderiza os `<td>`s da linha. `jx-neighborhood-row` usa `display:contents` no host para que seus `<td>`s sejam filhos efetivos de `<tr>` (semântica de tabela preservada).
- **Máscara monetária própria** (`shared/util/money`): `maskBrl`/`parseBrl`/`formatBrl` para `R$ 0,00` pt-BR com vírgula decimal — `inputmode="decimal"`, nunca `type="number"` cru para dinheiro (br/brazilian-forms).
- **Confirmação sensível** (saas-dashboard): diálogo `role="dialog"` lista os campos sensíveis alterados em before→after (mono) antes de chamar o PATCH (que o backend audita — Plan 01).
- **Migração da fila KYC para jx-data-table:** desejável mas NÃO obrigatória nesta task; não couber no orçamento → registrada como SUG-009 (sem redesenho de colunas). O primitivo está pronto para a próxima passada.

## Deviations from Plan

Nenhum desvio de comportamento. A migração opcional da fila KYC (tela 17/18) para `jx-data-table` ficou como SUG (o plano marcou como desejável, não obrigatória).

## Tech debt
- SUG-009: migrar `jx-kyc-queue-table` (Phase 5) para consumir `jx-data-table` numa próxima passada (sem redesenho).

## Verificação local
- `npx ng build` → OK. **Bundle initial: 598.30 KB raw / 160.93 KB gzip** (< 400 KB gzip budget de main).
- `npx ng test` (suíte completa) → **60 passed** (46 anteriores + 14 novos: data-table 5, area-config 4, neighborhoods 5).
- `npx ng lint` → All files pass.
- Hex check: `grep -rE "#[0-9A-Fa-f]{6}" src/features/admin/area-config src/features/admin/neighborhoods src/shared/components/data-table --include=*.scss | grep -v _tokens` → **0** (Gate 2).

## O que verificar ao vivo (visual — checkpoint do plano)
- Tela 21A (`/admin/config`): 4 fieldsets, máscara R$ nos pisos, erro de faixa no blur, diálogo de confirmação before→after, estados salvando/sucesso/erro — claro+dark.
- Tela 21B (`/admin/bairros`): catálogo sobre jx-data-table, badges de polígono, adicionar com/sem GeoJSON, remoção bloqueada (role=alert), estado vazio com CTA — claro+dark.
- axe sem violações críticas nas duas telas (claro+dark).

## Self-Check: PASSED
- data-table.component.ts, area-config.page.ts, neighborhoods.page.ts — FOUND. Commits b69912b, 35b1d61, ad0967f — FOUND.
