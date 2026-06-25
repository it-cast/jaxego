# CORRECAO-136 — Endereço de entrega sempre visível para o entregador

## O que mudou

### Backend (apps/api)
- **couriers/router.py**: Removida a lógica `revealed` que escondia endereço de entrega, número, complemento, coordenadas e dados do destinatário antes da coleta. Agora todos os campos são retornados em qualquer estado da entrega.
- **dispatch/schemas.py**: `OfferOut` agora inclui `dropoff_address` e `dropoff_number` para o entregador ver o destino já na oferta.
- **dispatch/service.py**: Construção do `OfferOut` agora envia `dropoff_address` e `dropoff_number` da entrega.

## Arquivos alterados
- apps/api/app/couriers/router.py
- apps/api/app/dispatch/schemas.py
- apps/api/app/dispatch/service.py
