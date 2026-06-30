# CORRECAO-157 — Exibir média de avaliação (avg_stars) em vez de score badge

## Problema
A coluna "Score" em `/plataforma/pessoas` não exibia nada pois `score_level`
era sempre `null` no backend, impedindo o `jx-score-badge` de renderizar.

## O que mudou

### Backend (apps/api)
- **platform_admin/schemas.py**: `CourierSearchRow` substituiu `score_total`
  e `score_level` por `avg_stars: float | None`
- **platform_admin/service.py**: `search_couriers` passou a usar subquery
  correlacionada para calcular `avg_stars` em uma única query (eliminou N+1 —
  antes fazia uma query de rating por entregador)

### Frontend (apps/web)
- **platform-admin.service.ts**: Interface `CourierSearchRow` atualizada com
  `avg_stars: number | null` (removidos `score_total` e `score_level`)
- **pessoas.page.ts**:
  - Coluna renomeada de "Score" para "Avaliação"
  - Importados `FaIconComponent`, `faStar`, `DecimalPipe`
  - `iconStar = faStar` exposto para o template
- **pessoas.page.html**: Substituído bloco `jx-score-badge` por
  `<fa-icon [icon]="iconStar" /> {{ item.avg_stars | number:'1.1-1' }}`
  com fallback "Sem avaliação"

## Arquivos alterados
- apps/api/app/platform_admin/schemas.py
- apps/api/app/platform_admin/service.py
- apps/web/src/features/admin-plataforma/platform-admin.service.ts
- apps/web/src/features/admin-plataforma/pessoas.page.ts
- apps/web/src/features/admin-plataforma/pessoas.page.html
