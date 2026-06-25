# CORRECAO-147 — Endereço de entrega visível na oferta do app

## O que mudou

### Frontend (apps/app)
- **offer.models.ts**: Interface `OfferOut` agora inclui `dropoff_address` e `dropoff_number`
- **offer-sheet.component.ts**: Seção de entrega na oferta agora mostra o endereço completo (rua + número) na linha principal, com bairro + distância como hint abaixo. Removida a mensagem "(endereço completo após a coleta)"

## Arquivos alterados
- apps/app/src/features/entregador/oferta/offer.models.ts
- apps/app/src/features/entregador/oferta/offer-sheet.component.ts
