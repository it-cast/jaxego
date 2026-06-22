# Correção 063 — CRUD de Planos de assinatura no admin de plataforma

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend (API)

- `apps/api/app/plans/schemas.py` (criado)
- `apps/api/app/plans/service.py`
- `apps/api/app/platform_admin/router.py`

### Frontend (Admin web)

- `apps/web/src/features/admin-plataforma/planos.page.ts` (criado)
- `apps/web/src/features/admin-plataforma/planos.page.html` (criado)
- `apps/web/src/features/admin-plataforma/planos.page.scss` (criado)
- `apps/web/src/features/admin-plataforma/platform-admin.service.ts`
- `apps/web/src/layouts/plataforma-shell.component.ts`
- `apps/web/src/app/app.routes.ts`

## Problema

Os planos de assinatura existiam apenas como seed no banco e endpoint público de leitura (`GET /v1/plans`). Não havia interface para o admin da plataforma gerenciar (criar, editar, desativar) planos.

## Implementação

### Backend

- Schemas Pydantic: `PlanAdminRead` (com todos os campos incluindo `id`, `is_active`, `sort_order`), `PlanCreate`, `PlanUpdate`
- Funções no service: `list_all_plans` (inclui inativos), `get_plan_by_id`, `create_plan` (valida código único), `update_plan` (bloqueia edição do plano Free), `delete_plan` (soft-delete via `is_active=False`, bloqueia remoção do Free)
- 4 endpoints em `/v1/platform/plans` (require_platform_admin + TOTP):
  - `GET` — lista todos os planos (ativos e inativos)
  - `POST` — cria plano novo (201)
  - `PATCH /{plan_id}` — edita campos do plano
  - `DELETE /{plan_id}` — desativa plano (204, soft-delete)

### Frontend

- Nova rota `/plataforma/planos` com link "Planos" no menu lateral (ícone `faCreditCard`)
- Listagem com `jx-data-table`, filtro client-side por nome/código e status (todos/ativos/inativos)
- Botão "+ Adicionar" no header abre form de criação
- Colunas: Nome, Código, Preço (R$), Entregas/mês, Taxa (R$), Status, Ações
- Ícone de edição e delete em cada row (desabilitados para o plano Free)
- Delete com confirmação inline (mostra "Desativar?" com botões confirmar/cancelar)
- Badges de status (Ativo/Inativo) e badge "Free" no plano gratuito
- Form compartilhado para criar/editar com campos: código, nome, preço (centavos), entregas/mês, taxa (centavos), ordem, checkbox "ilimitado"
- Código é imutável na edição
- Feedback messages (sucesso/erro) com `role="status"`
- 4 métodos adicionados ao `PlatformAdminService`: `listPlans`, `createPlan`, `updatePlan`, `deletePlan`
- Interfaces: `PlanAdmin`, `PlanCreateBody`, `PlanUpdateBody`
