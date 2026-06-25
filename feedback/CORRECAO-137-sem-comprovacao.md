# CORRECAO-137 — Opção "Sem comprovação" na nova entrega

## O que mudou

### Backend (apps/api)
- **deliveries/schemas.py**: `ProofMethod` enum agora inclui `none`

### Frontend
- **delivery.models.ts** (packages/shared): `DeliveryProofMethod` inclui `'none'`
- **nova-entrega.page.html** (apps/web): Option "Sem comprovação" adicionada como primeira opção no select de comprovação
- **nova-entrega.page.ts** (apps/web): Cast do proof_method atualizado para incluir `'none'`

## Arquivos alterados
- apps/api/app/deliveries/schemas.py
- packages/shared/src/shared/models/delivery.models.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.html
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
