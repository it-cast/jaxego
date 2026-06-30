# CORRECAO-166 — Paginação /loja/entregas (20 itens/página)

## Página
`http://localhost:4200/loja/entregas`

## Arquivos alterados
- `apps/web/src/features/loja/entregas/entregas-list.page.ts`
- `apps/web/src/features/loja/entregas/entregas-list.page.html`
- `apps/web/src/features/loja/entregas/entregas-list.page.scss`

## O que mudou
- `PAGE_SIZE = 20` (server-side — o serviço já suportava `limit` e `offset`)
- `currentPage` signal + `totalPages` computed
- `load()` passa `limit` e `offset` ao serviço
- `filterAndLoad()` reseta página para 0 ao trocar filtros (estado/pagamento)
- `clearFilters()` também reseta página
- Template: controles de paginação com FA icons (chevronLeft/Right) abaixo da tabela
- SCSS: estilos `.jx-entregas__pagination`, `.jx-entregas__page-btn`, `.jx-entregas__page-info`

## Paginação
Server-side — backend já retornava `total` na resposta. Não requer rebuild do container.
