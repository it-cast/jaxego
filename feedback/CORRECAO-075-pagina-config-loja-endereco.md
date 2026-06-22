# Correção 075 — Página de configurações da loja + campo endereço

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Migration

- `apps/api/alembic/versions/0015_merchant_address.py` (criado) — adiciona coluna `address varchar(255)` nullable em `merchants`

### Backend (API)

- `apps/api/app/merchants/models.py` — campo `address` no model `Merchant`
- `apps/api/app/merchants/schemas.py` — schemas `MerchantProfileRead`, `MerchantProfileUpdate`
- `apps/api/app/merchants/router.py` — endpoints `GET /v1/merchants/profile` e `PATCH /v1/merchants/profile`
- `apps/api/app/auth/schemas.py` — campo `address` no `MeResponse`
- `apps/api/app/auth/service.py` — `resolve_surface` popula `address` para merchants

### Frontend (Loja web)

- `apps/web/src/features/loja/config/config.page.ts` (criado)
- `apps/web/src/features/loja/config/config.page.html` (criado)
- `apps/web/src/features/loja/config/config.page.scss` (criado)
- `apps/web/src/app/app.routes.ts` — rota `/loja/config`
- `apps/web/src/layouts/loja-shell.component.ts` — link "Configurações" no menu
- `packages/shared/src/core/auth/auth.models.ts` — campo `address` na interface `Me`
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts` — pickup_address pré-preenchido com `address` (fallback para `trade_name`)

## Problema

A loja não tinha como cadastrar seu endereço. O campo "Endereço de coleta" na nova entrega vinha vazio, e o lojista precisava digitar toda vez. Não existia página de configurações da empresa.

## Implementação

- Coluna `address` adicionada à tabela `merchants` via migration 0015
- Endpoints `GET/PATCH /v1/merchants/profile` para leitura e atualização do perfil (requer auth de merchant)
- Página `/loja/config` com form editável: nome da loja e endereço. E-mail e categoria exibidos como readonly
- `MeResponse` agora retorna `address` para merchants, usado no pré-preenchimento do pickup_address na nova entrega
- Lógica de pré-preenchimento: usa `address` se disponível, senão fallback para `trade_name`
