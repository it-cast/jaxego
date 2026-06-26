# CORRECAO-151 — Tela de entregadores e revisão KYC no admin de equipe

## O que mudou

### Backend (apps/api)
- **teams/team_admin_router.py**: Novos endpoints:
  - `GET /v1/team-admin/couriers/{id}` — detalhe do entregador com documentos
  - `GET /v1/team-admin/couriers/{id}/documents/{id}/view-url` — URL presigned da imagem do documento

### Frontend (apps/web)
- **equipe/equipe-kyc.service.ts** (novo): Service com métodos listCouriers, getCourier, viewUrl, approve, reject
- **equipe/entregadores.page.ts** (reescrito): Agora igual ao `/admin/entregadores` — DataTable com filtro (fila de validação / todos), busca por nome, paginação, botão "Revisar/Abrir" que navega para detalhe
- **equipe/kyc-detalhe.page.ts** (novo): Tela de revisão KYC — exibe dados do entregador, lista documentos com status, botão "Ver documento" (carrega imagem presigned), botões "Aprovar" e "Reprovar" para documentos pendentes
- **app.routes.ts**: Rota `/equipe/entregadores/:courierId` adicionada

## Arquivos criados
- apps/web/src/features/equipe/equipe-kyc.service.ts
- apps/web/src/features/equipe/kyc-detalhe.page.ts

## Arquivos alterados
- apps/api/app/teams/team_admin_router.py
- apps/web/src/features/equipe/entregadores.page.ts
- apps/web/src/app/app.routes.ts
