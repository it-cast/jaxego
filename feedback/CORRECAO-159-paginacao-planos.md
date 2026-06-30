# CORRECAO-159 — Paginação de 20 em 20 itens em Planos

## O que mudou

### /plataforma/planos
Paginação client-side (mesma estratégia de Áreas): carrega todos os planos
de uma vez e fatia com `computed` + `slice`.

- **planos.page.ts**:
  - Constante `PAGE_SIZE = 20`
  - Signal `page`, computed `paged` (slice do `filtered`) e `hasNext`
  - Método `goTo(delta)` — `applyFilter()` reseta para página 1
  - Importados `faChevronLeft`, `faChevronRight` e `computed`

- **planos.page.html**: `[rows]="paged()"` + controles Anterior / Página N / Próxima

- **planos.page.scss**: Estilos `.jx-planos__pager*`

## Arquivos alterados
- apps/web/src/features/admin-plataforma/planos.page.ts
- apps/web/src/features/admin-plataforma/planos.page.html
- apps/web/src/features/admin-plataforma/planos.page.scss
