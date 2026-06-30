# CORRECAO-165 — Paginação /admin/lojas ajustada para 20 itens

## Página
`http://localhost:4200/admin/lojas`

## Arquivo alterado
`apps/web/src/features/admin/lojas/lojas-list.page.ts`

## Mudança
`PAGE_SIZE` de `10` → `20`, igual a todas as demais páginas do admin.
Sem alteração no backend.
