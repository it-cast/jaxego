# Correção 091 — Observações do lojista exibidas na entrega ativa

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend (API)

- `apps/api/app/deliveries/schemas.py` — campo `notes` adicionado ao `CourierDeliveryOut`
- `apps/api/app/couriers/router.py` — `notes` incluído no builder `_courier_delivery_out`

### Frontend (App entregador)

- `apps/app/src/features/entregador/entregador.service.ts` — campo `notes` na interface `CourierDelivery`
- `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts` — exibe "📝 {notas}" no card de coleta quando houver observações

## Problema

O lojista podia preencher "Observações para o entregador" na criação da entrega, mas essa informação não aparecia no app do entregador.

## Correção

- `notes` agora flui do backend até o app na resposta `CourierDeliveryOut`
- Exibido com ícone 📝 no card de coleta da entrega ativa, em destaque (brand color, itálico)
- Só aparece se a entrega tiver observações preenchidas
