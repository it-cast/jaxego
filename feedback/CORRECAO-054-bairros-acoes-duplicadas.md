# Correção 054 — Coluna Ações duplicada em /admin/bairros

> **Classe:** COD/UI · **Data:** 2026-06-19

---

## Arquivos afetados

- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.ts`
- `apps/web/src/features/admin/neighborhoods/neighborhood-row.component.scss`

## Problema

A tela `/admin/bairros` exibia duas colunas de ações na tabela do catálogo de bairros.

Isso acontecia porque a página declarava manualmente uma coluna `actions` em `columns` e,
ao mesmo tempo, passava `[hasActions]="true"` para `jx-data-table`. O componente
compartilhado já cria a coluna extra de ações quando `hasActions` está ativo.

## Correção

- Removida a coluna manual `{ key: 'actions', label: 'Ações' }` da configuração de bairros
- Mantido `[hasActions]="true"` no template para preservar o cabeçalho/célula de ações gerados pelo componente compartilhado
- Ajustado o conteúdo da célula de ações para alinhar à esquerda, seguindo o alinhamento visual das outras colunas da tabela

## Resultado esperado

A tabela de `/admin/bairros` passa a renderizar apenas uma coluna de ações, com o botão
alinhado à esquerda e consistente com as demais colunas.
