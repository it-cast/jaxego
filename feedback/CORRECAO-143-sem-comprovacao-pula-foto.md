# CORRECAO-143 — Comprovação "none" finaliza entrega sem pedir foto

## O que mudou

### Backend (apps/api)
- **couriers/router.py**: Novo endpoint POST `/{courier_id}/deliveries/{delivery_id}/finalize-no-proof` que faz COLETADA → ENTREGUE → FINALIZADA em um step, sem exigir foto. Só funciona quando `proof_method = 'none'`

### Frontend (apps/app)
- **entregador.service.ts**: Novo método `finalizeNoProof(courierId, deliveryId)`
- **entrega-ativa.page.ts**: Botão "Cheguei no destino" agora verifica `proof_method`:
  - `none` → finaliza direto e navega para tela de conclusão
  - `photo` / `photo_reference` → navega para tela de comprovação (comportamento anterior)

## Arquivos alterados
- apps/api/app/couriers/router.py
- apps/app/src/features/entregador/entregador.service.ts
- apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts
