# CORRECAO-144 — Favoritos com avaliação real e sem placa do veículo

## O que mudou

### Backend (apps/api)
- **merchants/favorites.py**: `FavoriteRow` agora retorna `avg_stars` (média de avaliações dos últimos 90 dias) em vez de `vehicle_plate`. Endpoint `list_favorites` calcula a avaliação real via query na tabela `courier_ratings`.

### Frontend (apps/web)
- **favoritos.models.ts**: Interface `FavoriteRow` agora tem `avg_stars: number` em vez de `vehicle_plate`
- **favoritos.page.ts**: Score level calculado pela avaliação real (≥4.5 diamante, ≥4 ouro, ≥3 prata, ≥2 bronze, senão probation). Stats mostra "X ★" ou "Sem avaliação". Removidos `placeholderScoreLevel` e `plateStats`.

## Arquivos alterados
- apps/api/app/merchants/favorites.py
- apps/web/src/features/loja/favoritos/favoritos.models.ts
- apps/web/src/features/loja/favoritos/favoritos.page.ts
