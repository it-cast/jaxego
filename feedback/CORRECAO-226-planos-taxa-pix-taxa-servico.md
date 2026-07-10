# CORRECAO-226 — Planos: novos campos taxa_pix_cents e taxa_servico_cents

## Data
2026-07-09

## Mudança
Adição de `taxa_pix_cents` e `taxa_servico_cents` ao CRUD de planos.
`taxa_servico` substitui `taxa por entrega` no conceito — a loja escolhe entre
pagar a assinatura (Pro) e não ter taxa de serviço, ou ficar no plano Básico
(grátis) pagando R$ 1,00 por entrega.

## Novos planos (2)
| Plano  | Mensal   | taxa_pix | taxa_servico |
|--------|----------|----------|--------------|
| Básico | R$ 0,00  | R$ 0,50  | R$ 1,00      |
| Pro    | R$ 29,90 | R$ 0,50  | R$ 0,00      |

Planos antigos (inicio, profissional, sem_limite) desativados via seed.

## Arquivos alterados

### Backend
- `alembic/versions/0042_plan_taxa_pix_taxa_servico.py` — ADD COLUMN taxa_pix_cents, taxa_servico_cents (DEFAULT 0)
- `plans/models.py` — 2 novos Mapped columns
- `plans/schemas.py` — PlanAdminRead, PlanCreate, PlanUpdate com novos campos
- `merchants/schemas.py` — PlanRead (endpoint público) com novos campos
- `plans/router.py` — expõe taxa_pix_cents e taxa_servico_cents no /v1/plans
- `plans/service.py` — PLAN_SEEDS com 2 planos, create_plan/update_plan/seed_plans_if_missing atualizados
- `platform_admin/router.py` — create_plan e update_plan passam novos campos

### Frontend (web)
- `platform-admin.service.ts` — PlanAdmin, PlanCreateBody, PlanUpdateBody com novos campos
- `planos.page.ts` — colunas da tabela, emptyForm, showEdit, save atualizados
- `planos.page.html` — 2 novos inputs no form (taxa_pix, taxa_servico); 2 novas colunas na tabela
- `merchant.models.ts` — PlanDto com taxa_pix_cents e taxa_servico_cents

## Observações
- Migration copiada para container via `docker cp` (alembic/ não está em bind-mount)
- Seed rodado manualmente após restart do container
- `fee_cents` mantido no banco para compatibilidade com entregas existentes; migração gradual para `taxa_servico_cents` na lógica de despacho fica como dívida técnica futura
