# CORRECAO-122 — CRUD de equipes (teams) no admin de área

## O que mudou

### Backend (apps/api)
- **teams/models.py** (novo): Modelo `Team` com `id`, `area_id`, `name`, `deleted_at`, `created_at`, `updated_at`
- **teams/schemas.py** (novo): `TeamCreate`, `TeamUpdate`, `TeamRead`
- **teams/service.py** (novo): CRUD area-scoped — list, get, create, update, archive (soft-delete)
- **teams/router.py** (novo): Endpoints em `/v1/admin/teams` — GET (list), POST (create), PATCH (update), POST archive. Todos gated por `require_role("admin_area")` e scoped por `AreaScopeDep`
- **api/v1/router.py**: Router de teams registrado
- **alembic 0021**: Migration para criar tabela `teams`

### Frontend (apps/web)
- **admin/equipes/equipes.page.ts** (novo): Página CRUD com DataTable, formulário inline de criar/editar, arquivamento com confirmação. Mesmo padrão visual das outras páginas do admin.
- **app.routes.ts**: Rota `/admin/equipes` adicionada
- **admin-shell.component.ts**: Item "Equipes" com ícone `faPeopleGroup` adicionado ao menu lateral

## Arquivos criados
- apps/api/app/teams/__init__.py
- apps/api/app/teams/models.py
- apps/api/app/teams/schemas.py
- apps/api/app/teams/service.py
- apps/api/app/teams/router.py
- apps/api/alembic/versions/0021_teams.py
- apps/web/src/features/admin/equipes/equipes.page.ts

## Arquivos alterados
- apps/api/app/api/v1/router.py
- apps/web/src/app/app.routes.ts
- apps/web/src/layouts/admin-shell.component.ts
