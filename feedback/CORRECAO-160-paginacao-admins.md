# CORRECAO-160 — Paginação de 20 em 20 itens em Admins de Área

## O que mudou

### /plataforma/admins
Paginação client-side: carrega todos os admins de uma vez e fatia com
`computed` + `slice`.

- **admins.page.ts**:
  - Constante `PAGE_SIZE = 20`
  - Signal `page`, computed `paged` e `hasNext`
  - Método `goTo(delta)` — `applyFilter()` reseta para página 1
  - Importados `faChevronLeft`, `faChevronRight` e `computed`

- **admins.page.html**: `[rows]="paged()"` + controles Anterior / Página N / Próxima

- **admins.page.scss**: Estilos `.jx-admins__pager*`

## Arquivos alterados
- apps/web/src/features/admin-plataforma/admins.page.ts
- apps/web/src/features/admin-plataforma/admins.page.html
- apps/web/src/features/admin-plataforma/admins.page.scss
