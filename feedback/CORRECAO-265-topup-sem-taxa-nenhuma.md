# CORRECAO-265 — Recarga de saldo: SEM taxa nenhuma

## Data
2026-07-15

## Pedido
Reverteu o CORRECAO-264 na hora: "NÃO VAI TER TAXA NENHUMA, ele vai colocar
50, vai pagar 50, e vai receber 50. Não tem taxa nenhuma." Removida toda
lógica de taxa_pix/taxa_servico da recarga de saldo — não é só "taxa
descontada em vez de somada" (como ficou no 264), é **zero taxa**.

## O que mudou

**Backend**
- `apps/api/app/merchants/router.py::create_credit_topup` — não chama mais
  `_active_plan_taxas`. `total_cents = net_amount_cents = body.amount_cents`,
  os três são sempre o mesmo valor. Removida a validação `topup_below_fees`
  (não existe mais — não tem como um valor "não cobrir taxas" quando não há
  taxa).
- Removido o endpoint `GET /v1/merchants/plan-taxas` inteiro — só existia pra
  alimentar a prévia de taxas do modal, que não existe mais.
- Removida a função `_active_plan_taxas()` inteira — a docstring dizia que
  era reusada em `deliveries/router.py::teams_for_address`, mas confirmei
  (`grep`) que lá tem uma implementação própria inline; a função ficou
  100% órfã depois de tirar as outras duas chamadas.
- `apps/api/app/merchants/schemas.py::CreditTopupResponse` — removidos os
  campos `taxa_pix_cents`, `taxa_servico_cents`, `total_cents` (redundante
  com `amount_cents` agora que são sempre iguais).

**Frontend** (`apps/web/src/features/loja/financeiro/saldo.page.ts/.html`)
- Removidos os signals `topupTaxaPixCents`, `topupTaxaServicoCents`,
  `topupTotalCents`, o computed `topupExpectedNetCents`, o método
  `loadPlanTaxas()` e a chamada dele em `openTopupModal()`.
- `topupValid` voltou a ser só `amount >= mínimo`.
- Modal: breakdown virou uma linha só — "Total a pagar via PIX" = valor
  digitado. Sem menção a taxa em lugar nenhum.

## Validado
- `docker compose exec api python -c "import app.merchants.router; import
  app.merchants.schemas; import app.main"` — import limpo.
- `ng build web` — verde, zero warning novo.
- `grep` por `taxa_pix`/`taxa_servico`/`plan-taxas` nos arquivos de saldo —
  zero ocorrência sobrando.
- API reiniciada, `/health` ok.

## Não testado
Fluxo real de pagamento (criar PIX de R$50 e confirmar que exatamente R$50
cai no saldo) — só validei import + build. Recomendo um teste real pequeno.

## Tech debt (herdado, não mudou aqui)
- `CREDIT_TOPUP_MIN_CENTS` continua em 1 centavo (temporário, era R$5) —
  reverter antes de produção.
