# CORRECAO-248 — Estorno do PIX + devolução de saldo ao cancelar entrega

## Data
2026-07-13

## Pedido
Regra dada pelo usuário para o cancelamento de entrega paga via `platform_pix`:
- Entrega saiu por R$5, pago PIX de R$5 → estornar o PIX de R$5 (endpoint
  confirmado pela Safe2Pay: `DELETE /v2/pix/cancel/{idTransaction}`, token da
  ITCAST filha).
- Entrega saiu por R$5, sendo R$2 de saldo → estornar o PIX de R$3 (só o que
  foi realmente cobrado no gateway) e devolver os R$2 pro saldo da loja.

## Desenho
Duas devoluções independentes, disparadas no cancelamento (`POST
/v1/deliveries/{id}/cancel`):

1. **Saldo usado** (`credit_applied_cents`) — devolução LOCAL e SÍNCRONA (não
   depende de nenhuma API externa). Novo `kind="reversal"` no
   `merchant_credit_ledger` (positivo), idempotente por `delivery_id`.
2. **PIX cobrado** (`platform_charges.amount_cents` — já é só a parte que o
   Safe2Pay recebeu, o desconto do saldo nunca passa pelo PIX) — estorno
   ENFILEIRADO (arq), mesmo padrão do repasse ao entregador (CORRECAO-241/242):
   nunca bloqueia a resposta do cancelamento, degrada graciosamente em falha
   da Safe2Pay (sem retry automático — TD, igual ao payout). O status final
   (`platform_charges.status = "refunded"`) chega pelo webhook já existente
   (`event_status "6"`, CORRECAO-243) — o disparo do estorno NUNCA marca o
   status ele mesmo, pra não competir com o webhook.

### Escopo: só no cancelamento gratuito (RN-004 cost=0)
O cancelamento hoje só é exposto na UI em `CRIADA` (RN-004 custo zero). O
state machine também permite cancelar em `ACEITA`/`COLETADA` (custo 50%/100%+
taxa), mas isso não está exposto em produto. Por segurança, o estorno
integral do PIX e a devolução do saldo só disparam quando
`cancel_cost_cents == 0` — devolver 100% num cancelamento pós-aceite
brigaria com o custo RN-004 já pensado pro entregador. Se esse caminho for
exposto no futuro, precisa de decisão de produto (TD).

## Arquivos

### Backend
- `app/payments/safe2pay_adapter.py` — novo `_delete_v2()` (DELETE com o
  mesmo wrapper `HasError` do POST v2); `refund()` agora usa o contrato
  confirmado pra Pix: `DELETE {api_url}/v2/pix/cancel/{idTransaction}`, sem
  campo de valor (só estorno total). Estorno de cartão continua
  `[ASSUMIDO]`, fora do escopo deste pedido.
- `app/merchants/models.py` — novo `kind="reversal"` em
  `MERCHANT_CREDIT_KINDS` (sem constraint no banco, só documentado).
- `app/merchants/credit.py` — `reverse_consumption()` (idempotente por
  `delivery_id` + `kind="reversal"`).
- `app/deliveries/refund.py` (novo) — `refund_delivery_on_cancel()`: busca a
  cobrança da entrega, dispara o estorno se `status == "paid"` e
  `method == "pix"`, nunca marca status ela mesma.
- `app/workers/refund.py` (novo) — `refund_delivery_task` (entrypoint arq) +
  `enqueue_refund()` (best-effort, espelha `workers/payout.py`).
- `app/workers/settings.py` — registrado `refund_delivery_task`.
- `app/deliveries/service.py::cancel_delivery` — devolve o saldo inline
  (síncrono) quando `cost == 0 and credit_applied_cents > 0`.
- `app/deliveries/router.py::cancel_delivery` — enfileira `enqueue_refund`
  depois do commit, só quando `cancel_cost_cents == 0`.

### Frontend
- `apps/web/.../financeiro/saldo.page.ts` — extrato reconhece o novo kind
  `reversal` ("Saldo devolvido (cancelamento)").

## Build
- `docker compose exec api python -c "import ..."` — todos os módulos novos
  e alterados importam limpo.
- API + worker reiniciados; worker registrou `refund_delivery_task` no boot
  (log confirmado: "Starting worker for 44 functions: ... refund_delivery_task").
- `ng build web` — verde.
- Sem migration nova (nenhuma coluna de banco mudou — só um novo valor de
  `kind`, coluna já é `String(16)` livre).

## Não testado end-to-end
Não disparei um estorno real contra a Safe2Pay nesta sessão (envolve
movimentação de dinheiro real e não há entrega de teste paga em estado
cancelável agora). Fica para o próximo teste do usuário — se falhar, checar
logs por `delivery.refund_pending` (erro da Safe2Pay) ou `refund.enqueue_failed`
(fila fora do ar).

## Tech debt em aberto
- Sem retry automático se o estorno falhar na Safe2Pay (mesmo padrão aceito
  pro payout, CORRECAO-241/242) — precisa de reconciliação manual se acontecer.
- Cancelamento pós-aceite (`ACEITA`/`COLETADA`, custo RN-004 > 0) não dispara
  estorno nem devolve saldo — decisão de produto em aberto se esse caminho
  for exposto no futuro.
- Estorno de cartão continua `[ASSUMIDO]` (não confirmado com a Safe2Pay).
