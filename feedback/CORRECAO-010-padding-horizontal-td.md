# Correção 010 — Padding horizontal dos `<td>` colado na borda da tabela

> **Classe:** COD · **Data:** 2026-06-15 · **Relacionada:** Correção 009

---

## Arquivo afetado

- `apps/web/src/styles/global.scss`

## Problema

Mesmo após a correção 009, o texto das células estava colado na borda esquerda da tabela. O `padding` definido em `data-table.component.scss` para `tbody td` não era aplicado porque os `<td>` são conteúdo projetado (via `ng-template` do componente pai) e carregam o atributo de encapsulamento do pai, não do `data-table`.

## Correção

Regra `.jx-data-table tbody td { padding: var(--jx-space-3) var(--jx-space-4) }` movida para `global.scss`, que não tem encapsulamento Angular e aplica o estilo independente de qual componente projetou o `<td>`.
