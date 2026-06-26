# CORRECAO-150 — Acesso do responsável da equipe (admin de equipe)

## O que mudou

### Backend (apps/api)
- **auth/service.py**: `resolve_surface` agora detecta responsáveis de equipe (surface="equipe") entre admin de área e courier. Retorna `team_id`
- **auth/schemas.py**: `MeResponse` agora inclui `team_id`
- **teams/team_admin_router.py** (novo): Endpoints para admin de equipe:
  - `GET /v1/team-admin/dashboard` — KPIs (entregadores, online, pendentes, entregas hoje)
  - `GET /v1/team-admin/couriers` — lista entregadores da equipe com documentos
  - `POST /v1/team-admin/couriers/{id}/documents/{id}/approve` — aprovar documento
  - `POST /v1/team-admin/couriers/{id}/documents/{id}/reject` — reprovar documento
  - `GET /v1/team-admin/deliveries` — entregas da equipe paginadas
- **api/v1/router.py**: Router de team-admin registrado

### Frontend (apps/web)
- **auth.models.ts**: Surface `'equipe'` e `team_id` adicionados
- **auth.service.ts**: `surfaceHome('equipe')` → `/equipe`
- **equipe-shell.component.ts** (novo): Shell com sidebar (Painel, Entregadores, Entregas)
- **equipe/dashboard.page.ts** (novo): Dashboard com cards de KPIs
- **equipe/entregadores.page.ts** (novo): Lista entregadores com documentos e botões aprovar/reprovar
- **equipe/entregas.page.ts** (novo): Tabela de entregas paginada
- **app.routes.ts**: Rotas `/equipe/*` com guard de auth

## Fluxo
1. Admin de área cria equipe com email/senha do responsável
2. Responsável faz login com email/senha → detectado como surface "equipe"
3. Roteado para `/equipe/painel` com dashboard, entregadores e entregas

## Arquivos criados
- apps/api/app/teams/team_admin_router.py
- apps/web/src/layouts/equipe-shell.component.ts
- apps/web/src/features/equipe/dashboard.page.ts
- apps/web/src/features/equipe/entregadores.page.ts
- apps/web/src/features/equipe/entregas.page.ts

## Arquivos alterados
- apps/api/app/auth/service.py
- apps/api/app/auth/schemas.py
- apps/api/app/api/v1/router.py
- packages/shared/src/core/auth/auth.models.ts
- packages/shared/src/core/auth/auth.service.ts
- apps/web/src/app/app.routes.ts
