# CORRECAO-158 — Paginação de 20 em 20 itens em Pessoas e Áreas

## O que mudou

### /plataforma/pessoas (Entregadores e Lojas)
Paginação server-side: cada troca de página dispara nova request com
`limit=20` e `offset=(página-1)*20`.

- **pessoas.page.ts**:
  - Constante `PAGE_SIZE = 20`
  - Signals separados por aba: `courierPage`, `courierHasNext`,
    `merchantPage`, `merchantHasNext`
  - Métodos `loadCouriers()` e `loadMerchants()` com `limit`/`offset`
  - Métodos `courierGoTo(delta)` e `merchantGoTo(delta)`
  - Buscar ou trocar de aba reseta para página 1
  - Detecta última página: se API retorna < 20 itens, "Próxima" fica
    desabilitado
  - Importados `faChevronLeft`, `faChevronRight`

- **pessoas.page.html**: Controles Anterior / Página N / Próxima abaixo de
  cada tabela (cada aba tem seu próprio paginador)

- **pessoas.page.scss**: Estilos `.jx-plat-people__pager`,
  `.jx-plat-people__pager-btn`, `.jx-plat-people__pager-info`,
  `.jx-plat-people__stars`

### /plataforma/areas (Áreas)
Paginação client-side: carrega todas as áreas de uma vez e fatia com
`computed` (áreas são poucas; não justifica server-side).

- **areas.page.ts**:
  - Constante `PAGE_SIZE = 20`
  - Signal `page`, computed `paged` (slice do `filtered`) e `hasNext`
  - Método `goTo(delta)` — `applyFilter()` reseta para página 1
  - Importados `faChevronLeft`, `faChevronRight`

- **areas.page.html**: `[rows]="paged()"` + controles de paginação

- **areas.page.scss**: Estilos `.jx-areas__pager*`

## Arquivos alterados
- apps/web/src/features/admin-plataforma/pessoas.page.ts
- apps/web/src/features/admin-plataforma/pessoas.page.html
- apps/web/src/features/admin-plataforma/pessoas.page.scss
- apps/web/src/features/admin-plataforma/areas.page.ts
- apps/web/src/features/admin-plataforma/areas.page.html
- apps/web/src/features/admin-plataforma/areas.page.scss
