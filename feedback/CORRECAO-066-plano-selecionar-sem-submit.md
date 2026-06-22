# Correção 066 — Botão do card de plano: "Selecionar" em vez de "Continuar no Free"/"Escolher..."

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `packages/shared/src/shared/components/plan-card/plan-card.component.ts`
- `packages/shared/src/shared/components/plan-card/plan-card.component.scss`
- `apps/web/src/features/loja/cadastro/cadastro.page.ts`

## Problema

Cada card de plano tinha um botão com texto variável ("Continuar no Free", "Escolher Início", etc.) que ao clicar disparava o submit do cadastro imediatamente. O esperado é que o botão apenas selecione o plano, e o submit aconteça no botão "Ativar loja".

## Correção

- Botão do card agora exibe "Selecionar" (não selecionado) ou "Selecionado" (selecionado, desabilitado)
- Card selecionado: botão fica com fundo brand (`--fill`) e `disabled`
- `choosePlan()` no cadastro agora só faz `selectedPlan.set()` — não chama mais `submit()`
- O submit acontece apenas pelo botão "Ativar loja" (`next()` → `submit()`)
- Removido getter `ctaLabel` que ficou sem uso
