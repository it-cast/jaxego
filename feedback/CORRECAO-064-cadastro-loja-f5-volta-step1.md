# Correção 064 — F5 no cadastro da loja voltava para step Planos em vez do step 1

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/features/loja/cadastro/cadastro.page.ts`

## Problema

Ao dar F5 na página `/loja/cadastro`, o wizard restaurava o step salvo no `sessionStorage` (ex: step 3 — Plano). O comportamento esperado é sempre voltar para o step 1 (Identificação), mantendo apenas os dados do formulário preenchidos.

## Correção

- Em `restoreDraft()`, removida a linha que restaurava `this.current.set(step)`. Agora o draft restaura apenas os valores do formulário; o step sempre começa em 0 (Identificação).
