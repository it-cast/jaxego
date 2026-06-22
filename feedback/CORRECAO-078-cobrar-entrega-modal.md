# Correção 078 — Botão "Cobrar entrega" com modal de método de cobrança

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Migration

- `apps/api/alembic/versions/0016_courier_collection_method.py` (criado) — coluna `courier_collection_method varchar(16)` nullable em `deliveries`

### Backend (API)

- `apps/api/app/deliveries/models.py` — campo `courier_collection_method` no model
- `apps/api/app/deliveries/schemas.py` — campo `courier_collection_method` no `CourierDeliveryOut`
- `apps/api/app/couriers/router.py` — endpoint `PATCH /v1/couriers/{id}/deliveries/{id}/collection-method` + campo no builder `_courier_delivery_out`

### Frontend (App entregador)

- `apps/app/src/features/entregador/entregador.service.ts` — campo `courier_collection_method` na interface `CourierDelivery` + método `setCollectionMethod()`
- `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts` — botão "Cobrar entrega", modal bottom-sheet, badge de método escolhido

## Problema

Na entrega ativa, o entregador não tinha como registrar como cobraria do destinatário antes de comprovar a entrega.

## Implementação

- Quando a entrega está em `COLETADA` e sem `courier_collection_method` definido, exibe o botão "Cobrar entrega" no lugar do botão de avanço
- Ao clicar, abre um modal bottom-sheet com 2 opções:
  - 💵 "Recebi em mãos" (dinheiro/PIX direto) → salva `in_hand`
  - 📱 "Cobrar com PIX" (QR Code) → salva `pix_app`
- Após escolher, o método é salvo via PATCH no backend e a página recarrega
- Com o método definido, o botão volta a ser o de avanço normal ("Cheguei no destino — comprovar")
- Badge exibe o método escolhido abaixo do botão
