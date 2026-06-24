# CORRECAO-115 — Endereço de coleta com rua, número e bairro

## O que mudou

### Backend (apps/api)
- **auth/schemas.py**: `MeResponse` agora inclui `address_number` e `address_neighborhood`
- **auth/service.py**: `resolve_surface` retorna os 3 campos do merchant

### Frontend
- **auth.models.ts** (packages/shared): Interface `Me` agora inclui `address_number` e `address_neighborhood`
- **nova-entrega.page.ts** (apps/web): Endereço de coleta composto como `"Rua, 123, Bairro"` em vez de só `address`. Fallback para `trade_name` se nenhum campo preenchido.

## Arquivos alterados
- apps/api/app/auth/schemas.py
- apps/api/app/auth/service.py
- packages/shared/src/core/auth/auth.models.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
