# CORRECAO-141 — Remover exigência de foto na coleta

## O que mudou

### Backend (apps/api)
- **couriers/router.py**: Novo endpoint POST `/{courier_id}/deliveries/{delivery_id}/collect` que faz a transição ACEITA → COLETADA diretamente, sem exigir foto de comprovação

### Frontend (apps/app)
- **entregador.service.ts**: Novo método `markCollected(courierId, deliveryId)` que chama o endpoint de coleta
- **entrega-ativa.page.ts**: Botão "Coletei" agora faz POST direto para marcar como coletada (sem navegar para tela de foto). Step label "Coletar e fotografar" trocado para "Coletar"

## Arquivos alterados
- apps/api/app/couriers/router.py
- apps/app/src/features/entregador/entregador.service.ts
- apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts
