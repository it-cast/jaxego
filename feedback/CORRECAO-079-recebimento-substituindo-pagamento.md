# Correção 079 — "Pagamento da corrida" substituído por "Recebimento" na nova entrega

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Migration

- `apps/api/alembic/versions/0017_receipt_method.py` (criado) — coluna `receipt_method varchar(16)` nullable em `deliveries`

### Backend (API)

- `apps/api/app/deliveries/models.py` — campo `receipt_method` no model
- `apps/api/app/deliveries/schemas.py` — campo `receipt_method` no `CreateDeliveryBody` e `CourierDeliveryOut`, `payment_method` com default `direct`
- `apps/api/app/deliveries/service.py` — salva `receipt_method` na criação
- `apps/api/app/couriers/router.py` — inclui `receipt_method` no builder `_courier_delivery_out`

### Frontend (Loja web)

- `apps/web/src/features/loja/entregas/nova-entrega.page.html` — seção "Pagamento da corrida" substituída por "Recebimento" com 3 opções: Dinheiro, Máquina da loja, Aplicativo
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts` — form control `receipt_method` + signal `receiptMethod`, submit envia `receipt_method` e hardcoda `payment_method: 'direct'`
- `packages/shared/src/shared/models/delivery.models.ts` — campo `receipt_method` na interface `CreateDeliveryRequest`

### Frontend (App entregador)

- `apps/app/src/features/entregador/entregador.service.ts` — campo `receipt_method` na interface `CourierDelivery`
- `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts` — badge de recebimento exibido ao lado do estado (💵 Dinheiro / 💳 Máquina da loja / 📱 Aplicativo)

## Problema

A seção "Pagamento da corrida" oferecia opções (Direto/PIX/Cartão) que se referiam ao pagamento da taxa de entrega para a plataforma, não ao recebimento do pedido pelo entregador. O lojista precisava informar como o cliente vai pagar o pedido.

## Correção

- Seção substituída por "Recebimento" com 3 opções: `dinheiro`, `maquina_loja`, `aplicativo`
- `payment_method` mantido no banco com valor fixo `direct` (não removido para não quebrar queries existentes)
- Informação de recebimento exibida no app do entregador como badge na entrega ativa
