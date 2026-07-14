# CORRECAO-246 — Saldo/crédito da loja (opt-in) por sobra/falta na entrega

## Data
2026-07-13

## Pedido
1. Se sobrar dinheiro (entregador que aceitou cobra menos que o valor pago no
   PIX antecipado), a diferença vira saldo positivo pra loja.
2. Se faltar (entregador mais caro aceita depois, via redespacho/pool), a
   diferença vira saldo negativo — não bloqueia novas entregas, compensa
   sozinho na próxima sobra.
3. **Correção do desenho original**: o uso do saldo é opt-in — a loja escolhe
   SE quer usar e QUANTO quer usar como desconto numa entrega nova (não é
   consumo automático). Escolha feita no step 2 do cadastro de nova entrega.

## Desenho

### Apuração (sobra/falta) — na FINALIZAÇÃO da entrega
Não na aceitação — pra não conflitar com o estorno parcial de cancelamento
(RN-004), que já tem sua própria lógica. `Delivery.pix_courier_price_cents`
(setado pelo SERVIDOR na criação, nunca confiado do cliente — é
`max(eligible_online_prices_cents(...))`, já calculado antes pra
`no_couriers_warning`) é comparado com `Delivery.price_cents` (preço do
entregador que realmente aceitou) nos 4 pontos que já disparam o repasse
automático (CORRECAO-241/242):
- `proofs/router.py::submit_proof` / `submit_reference`
- `couriers/router.py::finalize_no_proof`
- `workers/lifecycle.py::finalize_deliveries` (cron 24h)

Diferença positiva → crédito. Negativa → débito. Zero → nenhum lançamento.
Idempotente (checa se já existe um lançamento `reconciliation` pra aquela
entrega antes de gravar).

### Consumo (opt-in) — na CRIAÇÃO de uma entrega nova
A loja vê o saldo disponível e digita quanto quer usar (nunca pré-preenchido,
nunca aplicado sozinho). O valor é reclampado no SERVIDOR contra o saldo real
(sob lock) e contra o total da cobrança — nunca confia no número do cliente.
Se o saldo cobrir 100% da cobrança, a entrega nasce direto em `CRIADA` (sem
gerar PIX nenhum, sem esperar `AGUARDANDO_PAGAMENTO`).

## Tabela nova: `merchant_credit_ledger`
Extrato append-only (mesmo padrão de `EscrowLedger`/`Withdrawal`): saldo é
sempre DERIVADO (soma sob `FOR UPDATE`), nunca um campo solto — evita corrida
entre duas entregas mexendo no saldo da mesma loja ao mesmo tempo. Campos:
`merchant_id`, `delivery_id` (origem do lançamento), `kind`
(`reconciliation`/`consumption`), `amount_cents` (sinal: + crédito / - débito),
`reason`.

## Arquivos

### Migration
`alembic/versions/0047_merchant_credit_ledger.py` — tabela `merchant_credit_ledger`
+ colunas `deliveries.pix_courier_price_cents` e `deliveries.credit_applied_cents`.

### Backend
- `app/merchants/models.py` — model `MerchantCreditLedger`.
- `app/merchants/credit.py` (novo) — `available_credit_cents`, `preview_credit_cents`
  (clampa ANTES da entrega existir), `record_consumption` (grava o lançamento
  DEPOIS que a entrega tem id — mesma trava/transação, sem corrida),
  `reconcile_delivery_credit`, `list_ledger`.
- `app/merchants/router.py` — `GET /v1/merchants/credit-balance`,
  `GET /v1/merchants/credit-ledger` (self-only via `CurrentUser`, mesmo padrão
  de `/profile`).
- `app/deliveries/models.py` — `pix_courier_price_cents`, `credit_applied_cents`.
- `app/deliveries/schemas.py` — `CreateDeliveryBody.credit_applied_cents`;
  `CreateDeliveryResponse.credit_applied_cents` + `final_pix_amount_cents`.
- `app/deliveries/service.py::create_delivery` — calcula o preço máximo
  elegível server-side, faz o preview do crédito ANTES de decidir o estado
  inicial (CRIADA vs AGUARDANDO_PAGAMENTO), grava o consumo depois que a
  entrega tem id, gera o PIX só pelo valor final (após desconto) ou pula o
  PIX inteiro se o saldo cobriu tudo.
- `app/proofs/router.py`, `app/couriers/router.py`, `app/workers/lifecycle.py`
  — chamada a `reconcile_delivery_credit` nos 4 pontos de finalização, antes
  do commit (atômico com a transição pra FINALIZADA).

### Frontend (loja)
- `nova-entrega.page.ts/html/scss` — step 2 ganha bloco "Saldo disponível"
  (só aparece se saldo > 0) com input de quanto usar (máscara BRL, botão
  "Usar tudo", botão "Limpar"), recalcula o total em tempo real, mostra no
  modal de confirmação de PIX também. Envia `credit_applied_cents` escolhido
  pela loja (não o máximo) no payload de criação.
- `financeiro/saldo.page.ts/html/scss` (nova) — tela "Meu saldo": card com
  saldo atual (`jx-money`, com aviso se negativo que não bloqueia nada) +
  extrato (`jx-data-table`) com data, motivo e valor de cada lançamento.
  Rota `/loja/saldo`, link no menu lateral (`loja-shell.component.ts`).
- `packages/shared/src/shared/models/delivery.models.ts` — campos novos em
  `CreateDeliveryRequest`/`CreateDeliveryResponse`.

## Validado
Testado direto contra o banco (sem custo/risco — é cálculo interno, não
mexe em Safe2Pay), com dados descartáveis removidos ao final:
- Saldo inicial 0 → crédito manual de R$10 → saldo 1000.
- `preview_credit_cents`: pedir R$20 pra abater R$4,50 → aplica só 450
  (nunca mais que a cobrança). Pedir R$2 pra abater R$4,50 → aplica 200
  (respeita a escolha da loja, não força o máximo).
- Reconciliação sobra: entregador cobrou R$2, PIX pagou R$3 → +R$1 no saldo.
  Rodado 2x → não duplica (idempotente).
- Reconciliação falta: entregador cobrou R$4, PIX pagou R$3 → -R$1 no saldo.
- Build do backend (imports limpos, API+worker healthy) e do web
  (`ng build web`) verdes.

## Tech debt / pontos em aberto
- Sem tela de admin/plataforma pra ver saldos agregados de todas as lojas —
  só a própria loja vê o dela.
- `pix_courier_price_cents` só é preenchido em entregas `platform_pix` criadas
  a partir de agora — entregas antigas ficam `NULL` (sem reconciliação
  retroativa, como esperado).
