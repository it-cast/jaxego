# Correção 072 — CRUD de administradores de área na plataforma

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend (API)

- `apps/api/app/areas/service.py` — funções `list_area_admins`, `create_area_admin_with_user`, `update_area_admin`, `remove_area_admin`
- `apps/api/app/areas/schemas.py` — schemas `AreaAdminCreateBody`, `AreaAdminUpdateBody`, `AreaAdminRead` (atualizado com `area_name` e `user_name`)
- `apps/api/app/platform_admin/router.py` — endpoints `GET/POST/PATCH/DELETE /v1/platform/area-admins`

### Frontend (Admin web)

- `apps/web/src/features/admin-plataforma/admins.page.ts` (criado)
- `apps/web/src/features/admin-plataforma/admins.page.html` (criado)
- `apps/web/src/features/admin-plataforma/admins.page.scss` (criado)
- `apps/web/src/features/admin-plataforma/platform-admin.service.ts` — interfaces e métodos `listAreaAdmins`, `createAreaAdmin`, `updateAreaAdmin`, `removeAreaAdmin`
- `apps/web/src/layouts/plataforma-shell.component.ts` — link "Admins de área" no menu (ícone `faUserShield`)
- `apps/web/src/app/app.routes.ts` — rota `/plataforma/admins`

## Problema

Não existia interface para gerenciar administradores de área. A única forma era designar um usuário existente via campo inline na antiga tela de áreas, e o usuário precisava já ter conta no sistema.

## Implementação

### Backend

- `list_area_admins`: join de `area_admins` + `users` + `areas` para retornar nome, email e nome da área em uma query
- `create_area_admin_with_user`: se o email já existe, vincula à área; se não existe, cria o usuário (com hash de senha) e vincula. Valida duplicata de vínculo
- `update_area_admin`: atualiza papel e/ou área do admin
- `remove_area_admin`: hard delete do vínculo (não do usuário)
- 4 endpoints em `/v1/platform/area-admins` (require_platform_admin + TOTP)

### Frontend

- Mesma estrutura visual de planos/áreas (DataTable + filtro + form + editar/remover)
- Colunas: Nome, E-mail, Área, Papel, Ações
- Form de criação: seleciona área, papel, nome, e-mail e senha (cria conta + vínculo)
- Form de edição: apenas área e papel (dados do usuário não editáveis)
- Badges de papel: Dono (vermelho), Gestor (brand), Leitura (cinza)
- Busca client-side por nome, email ou área
- Remoção com confirmação inline
