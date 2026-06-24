# CORRECAO-118 — Nº do pedido obrigatório quando comprovação é foto + nº do pedido

## O que mudou

### Frontend (apps/web)
- **nova-entrega.page.ts**: Quando `proof_method` muda para `photo_reference`, o campo `reference_number` recebe `Validators.required`. Quando volta para `photo`, o validator é removido. Isso impede criar entrega sem nº do pedido quando a comprovação exige.

## Arquivos alterados
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
