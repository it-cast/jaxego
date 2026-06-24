# CORRECAO-114 — Campos de endereço separados no cadastro e config da loja

## O que mudou

### Backend (apps/api)
- **merchants/models.py**: Adicionados `address_number` (String 20) e `address_neighborhood` (String 120) na tabela merchants
- **alembic 0019**: Migration para adicionar as duas colunas
- **merchants/schemas.py**: `MerchantSignupBody`, `MerchantProfileRead` e `MerchantProfileUpdate` agora incluem `address`, `address_number` e `address_neighborhood`
- **merchants/service.py**: Signup salva os 3 campos de endereço
- **merchants/router.py**: GET e PATCH `/v1/merchants/profile` leem e salvam os 3 campos

### Frontend (apps/web)
- **merchant.models.ts**: `SignupRequest` agora envia `address`, `address_number`, `address_neighborhood`
- **cadastro.page.ts**: Submit envia `rua` → `address`, `numero` → `address_number`, `bairro` → `address_neighborhood`
- **config.page.ts**: Form com 3 campos de endereço, load e save atualizados
- **config.page.html**: Campos "Endereço (Rua, Av., ...)", "Número" e "Bairro" em row 50/50
- **config.page.scss**: Adicionado `.jx-config__row` para grid 2 colunas

## Arquivos alterados
- apps/api/app/merchants/models.py
- apps/api/alembic/versions/0019_merchant_address_number_neighborhood.py (novo)
- apps/api/app/merchants/schemas.py
- apps/api/app/merchants/service.py
- apps/api/app/merchants/router.py
- apps/web/src/features/loja/cadastro/merchant.models.ts
- apps/web/src/features/loja/cadastro/cadastro.page.ts
- apps/web/src/features/loja/config/config.page.ts
- apps/web/src/features/loja/config/config.page.html
- apps/web/src/features/loja/config/config.page.scss
