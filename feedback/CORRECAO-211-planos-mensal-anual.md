# CORRECAO-211 — Planos Mensais e Anuais

**Data:** 2026-07-07
**Sessão:** Continuação da sessão anterior (resumo de contexto)

## O que foi implementado

Feature completa de ciclo de cobrança Mensal/Anual nos planos.

### Decisão de arquitetura
- Um registro por plano (não dois registros separados)
- Dois campos de preço: `price_monthly_cents` + `price_annual_cents`
- Anual = mensal × 10 (2 meses grátis)

## Arquivos alterados

### Backend
- `apps/api/alembic/versions/0038_plan_price_monthly_annual.py` — migration: renomeia `price_cents` → `price_monthly_cents`, adiciona `price_annual_cents`
- `apps/api/alembic/versions/0037_merchant_address_zip_city_state.py` — corrigido `down_revision` para `"0036_courier_zona_ativo"` (cadeia alembic quebrada)
- `apps/api/app/plans/models.py` — `price_monthly_cents` + `price_annual_cents`
- `apps/api/app/plans/service.py` — PLAN_SEEDS, `create_plan`, `update_plan`, `seed_plans_if_missing`
- `apps/api/app/plans/schemas.py` — `PlanAdminRead`, `PlanCreate`, `PlanUpdate`
- `apps/api/app/merchants/schemas.py` — `PlanRead`: `preco_mensal_cents` + `preco_anual_cents`
- `apps/api/app/plans/router.py` — serializa ambos os preços
- `apps/api/app/platform_admin/router.py` — usa novos campos
- `apps/api/app/payments/subscriptions.py` — `_plan_amount_cents` usa campos separados (não multiplica mais)

### Frontend (shared)
- `packages/shared/src/shared/components/plan-card/plan-card.component.ts` — `Plan` interface atualizada; `@Input() cycle` controla qual preço exibir
- `packages/shared/src/shared/components/cycle-toggle/cycle-toggle.component.ts` — NOVO componente `jx-cycle-toggle` (Mensal/Anual + badge "2 meses grátis")
- `packages/shared/src/shared/components/index.ts` — exporta `CycleToggleComponent` + `BillingCycle`
- `packages/shared/src/shared/components/components.spec.ts` — testes atualizados
- `packages/shared/src/shared/components/upgrade-modal/upgrade-modal.stories.ts` — story data atualizado

### Frontend (web)
- `apps/web/src/features/loja/cadastro/cadastro.page.ts` — signal `cycle`, import CycleToggle, `this.cycle()` no subscribe
- `apps/web/src/features/loja/cadastro/cadastro.page.html` — `jx-cycle-toggle` acima da grade de planos
- `apps/web/src/features/loja/cadastro/merchant.models.ts` — `PlanDto` atualizado
- `apps/web/src/features/loja/cadastro/cadastro.stories.ts` — story data atualizado
- `apps/web/src/features/loja/plano/plano.page.ts` — signal `cycle`, import CycleToggle, `this.cycle()` nos dois submits (PIX + card)
- `apps/web/src/features/loja/plano/components/jx-plan-compare.component.ts` — `preco_mensal_cents` na lógica de upgrade/downgrade
- `apps/web/src/features/loja/plano/components/jx-plan-compare.stories.ts` — story data atualizado

## Problemas encontrados durante execução

1. **Cadeia alembic quebrada**: `0037` referenciava `down_revision = "0036"` mas o ID real era `"0036_courier_zona_ativo"` — corrigido + `docker cp` para o container (alembic não é bind-mounted)
2. **Migration 0037 parcialmente aplicada manualmente**: colunas `address_zip`/`address_state` já existiam no banco mas `address_city` não → adicionada manualmente + `alembic stamp 0037`
3. **`cycle` hardcoded como `'mensal'`** em 4 pontos de submit (2 no cadastro, 2 no plano) → corrigido para usar o signal

## Admin CRUD atualizado (sessão seguinte)
- `apps/web/src/features/admin-plataforma/platform-admin.service.ts` — `PlanAdmin`, `PlanCreateBody`, `PlanUpdateBody` atualizados
- `apps/web/src/features/admin-plataforma/planos.page.ts` — form, columns, `showEdit`, `save`, `emptyForm`
- `apps/web/src/features/admin-plataforma/planos.page.html` — campo "Preco anual" no formulário + coluna "Anual (R$)" na tabela

## Valores dos planos (após migration)
| Plano | Mensal | Anual |
|-------|--------|-------|
| Free | R$ 0 | R$ 0 |
| Início | R$ 49,00 | R$ 490,00 |
| Profissional | R$ 129,00 | R$ 1.290,00 |
| Sem Limite | R$ 299,00 | R$ 2.990,00 |
