# CORRECAO-145 — Favoritos com estrela FA simples, sem badge de score

## O que mudou

### Frontend (packages/shared)
- **favorite-row.component.ts**: Removido `ScoreChipComponent` e inputs `scoreLevel`, `scoreValue`, `stats`. Adicionado input `avgStars` com ícone FA `faStar` na cor brand + valor numérico ou "Sem avaliação"
- **favorite-row.component.scss**: Removido `.jx-favorite-row__stats`, adicionado `.jx-favorite-row__rating` e `.jx-favorite-row__star`

### Frontend (apps/web)
- **favoritos.page.ts**: Simplificado para passar apenas `[avgStars]="fav.avg_stars"`. Removidos `scoreLevel`, `scoreValue`, `stats`

## Arquivos alterados
- packages/shared/src/shared/components/favorite-row/favorite-row.component.ts
- packages/shared/src/shared/components/favorite-row/favorite-row.component.scss
- apps/web/src/features/loja/favoritos/favoritos.page.ts
