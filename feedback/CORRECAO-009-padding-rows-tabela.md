# Correção 009 — Padding insuficiente entre rows da tabela

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivo afetado

- `apps/web/src/shared/components/data-table/data-table.component.scss`

## Problema

As rows da `jx-data-table` estavam muito coladas. Tentativa de aumentar o `padding` no `td` não funcionou porque os `<td>` são conteúdo projetado via `@ContentChild` / `<ng-template #row let-item>` — eles carregam o atributo de encapsulamento do componente **pai** (ex: `visao-geral.page`), não do `data-table`. O Angular compila o selector `.jx-data-table tbody td` com o atributo do `data-table`, mas os elementos reais têm o atributo do pai — os estilos não batem.

## Correção

Adicionado `height: 52px` na regra `tbody tr`. O `<tr>` pertence ao template do próprio `data-table`, então o atributo de encapsulamento é aplicado corretamente e o estilo funciona. A `height` num `<tr>` com `border-collapse: collapse` funciona como altura mínima.
