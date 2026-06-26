# CORRECAO-152 — Foto do produto na entrega

## O que mudou

### Backend (apps/api)
- **deliveries/models.py**: Campo `image_key` (String 255, nullable) para armazenar a key do B2
- **alembic 0028**: Migration para adicionar coluna `image_key`
- **deliveries/router.py**: 
  - `POST /{id}/image/presign` — gera presigned PUT para upload direto ao B2 (pasta `deliveries/`)
  - `GET /{id}/image` — gera presigned GET para visualizar a imagem (loja)
- **couriers/router.py**: `GET /{courier_id}/deliveries/{id}/image` — presigned GET para o entregador ver a imagem
- **deliveries/schemas.py**: `has_image: bool` em todos os schemas de delivery
- Serialização atualizada nos routers de delivery e courier

### Frontend (apps/web)
- **nova-entrega.page.html**: Campo "Foto do produto (opcional)" com upload, preview e botão remover
- **nova-entrega.page.ts**: Métodos `onImageSelect`, `removeImage`, `uploadImage`. Após criar a entrega, faz upload via presigned PUT
- **nova-entrega.page.scss**: CSS do campo de upload (dashed border, preview com remove)

### Frontend (apps/app)
- **entregador.service.ts**: `has_image` na interface, método `deliveryImageUrl`
- **entrega-ativa.page.ts**: Exibe a foto do produto em um card "FOTO DO PRODUTO" quando `has_image` é true

## Arquivos alterados/criados
- apps/api/app/deliveries/models.py
- apps/api/alembic/versions/0028_delivery_image_key.py (novo)
- apps/api/app/deliveries/router.py
- apps/api/app/deliveries/schemas.py
- apps/api/app/couriers/router.py
- apps/web/src/features/loja/entregas/nova-entrega.page.html
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.scss
- apps/app/src/features/entregador/entregador.service.ts
- apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts
