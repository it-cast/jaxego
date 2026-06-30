# CORRECAO-155 — Exibir nome da área em vez do ID na tela de Pessoas

## Problema
Em `/plataforma/pessoas`, as colunas "Área" tanto de Entregadores quanto de Lojas
exibiam o `area_id` (número) em vez do nome legível da área.

## O que mudou

### Backend (apps/api)
- **platform_admin/schemas.py**: Adicionado campo `area_name: str` em `CourierSearchRow` e `MerchantSearchRow`
- **platform_admin/service.py**:
  - `search_couriers`: JOIN com `Area` via `Area.id == Courier.area_id`, inclui `area_name` no resultado
  - `search_merchants`: JOIN com `Area` via `Area.id == Merchant.area_id`, inclui `area_name` no resultado

### Frontend (apps/web)
- **platform-admin.service.ts**: Adicionado `area_name: string` em `CourierSearchRow` e `MerchantSearchRow`
- **pessoas.page.ts**: Colunas de área alteradas de `area_id` (numeric) para `area_name`
- **pessoas.page.html**: Template renderiza `item.area_name` em vez de `item.area_id` (ambas as abas)

## Arquivos alterados
- apps/api/app/platform_admin/schemas.py
- apps/api/app/platform_admin/service.py
- apps/web/src/features/admin-plataforma/platform-admin.service.ts
- apps/web/src/features/admin-plataforma/pessoas.page.ts
- apps/web/src/features/admin-plataforma/pessoas.page.html
