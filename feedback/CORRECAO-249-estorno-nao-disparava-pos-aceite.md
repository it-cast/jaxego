# CORRECAO-249 — Estorno do PIX não disparava em cancelamento pós-aceite

## Data
2026-07-13

## Pedido
1. Tirar o texto "Cobrar 50%" do botão de cancelar da loja.
2. "Fui testar o cancelamento e o pix não foi estornado. Veja qual erro deu"
   (estorno já tinha sido feito manualmente pelo usuário no painel Safe2Pay —
   não repeti a ação, só investiguei a causa).

## Causa raiz
CORRECAO-248 disparava o estorno automático e a devolução de saldo só quando
`cancel_cost_cents == 0`, assumindo que o cancelamento só era exposto na tela
ANTES do aceite (`entregas-list.page.ts`). Mas `entrega-detalhe.page.ts`
também expõe cancelar em `ACEITA`/`COLETADA` (botão "Cancelar (cobra
50%/100%)"). A entrega de teste (#112) foi cancelada a partir de `ACEITA`
(log: `from_state: "ACEITA", to_state: "CANCELADA"`, 19:44:16) — meu próprio
guard bloqueou o `enqueue_refund`, então o PIX nunca foi estornado
automaticamente.

Grep confirmou que `cancel_cost_cents` nunca virou uma cobrança real em
lugar nenhum do código (só é gravado, comentário original já dizia "charge
is Phase 11" — nunca implementado). Ou seja: o guard estava protegendo um
desconto que não existe. Resultado prático: o dinheiro do PIX ficava preso
(loja não recebia de volta, entregador também não recebia nada, já que o
repasse só dispara em FINALIZADA).

## Correção
- `app/deliveries/service.py::cancel_delivery` — devolução do saldo
  (`credit_applied_cents`) não depende mais de `cost == 0`.
- `app/deliveries/router.py::cancel_delivery` — `enqueue_refund` disparado
  em qualquer cancelamento (não só cost=0). `refund_delivery_on_cancel`
  (CORRECAO-248) já protege sozinho: só estorna se existir cobrança PIX
  `paid`, então cancelamentos sem PIX seguem sendo no-op.
- `apps/web/.../entrega-detalhe.page.ts::cancelLabel` — `'Cancelar (cobra
  50%)'` → `'Cancelar'` pro estado `ACEITA` (não mudei o texto de
  `COLETADA` — "cobra 100% + retorno" — por não ter sido pedido; mesma causa
  raiz se aplica lá, sinalizado abaixo).

## Não fiz
Não reprocessei o estorno da entrega #112 — o usuário já tinha feito manual
no painel Safe2Pay antes de eu investigar. Confirmado no banco que
`credit_applied_cents = 0` nela, então não havia saldo a devolver também.

## Tech debt / pontos em aberto
- O label de `COLETADA` ("Cancelar (cobra 100% + retorno)") tem a mesma
  causa raiz — hoje é só texto, não é cobrado. Não mexi por não ter sido
  pedido; avisar se quiser que eu tire/ajuste também.
- `cancel_cost_cents` continua sendo gravado mas não usado em lugar nenhum —
  segue como campo morto até a Phase 11 (faturamento) decidir se/como vai
  cobrar cancelamento pós-aceite de verdade.

## Build
- `docker compose exec api python -c "import ..."` — limpo.
- API + worker reiniciados.
- `ng build web` — verde.
