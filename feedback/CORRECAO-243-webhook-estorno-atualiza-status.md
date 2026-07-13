# CORRECAO-243 — Webhook de estorno (event_status "6") atualiza platform_charges.status

## Data
2026-07-13

## Contexto
Achado secundário da CORRECAO-242: o webhook da Safe2Pay recebe o evento de
estorno normalmente (confirmado em produção real: `event_status: "6"` na
entrega 107 depois do usuário estornar o PIX pelo painel da Safe2Pay), mas
`_process_event` só tratava `approved` (status 3/4) — o evento de estorno era
logado e ignorado. `platform_charges.status` ficava `paid` pra sempre, mesmo
com o dinheiro já devolvido de verdade.

## Fix
`app/payments/webhooks_router.py::_process_event`:
- Novo `refunded = event_status in {"6"}` (único código confirmado por
  evidência real até agora — comentário no código deixa isso explícito, caso
  a Safe2Pay use outros códigos pra variações de estorno/chargeback no
  futuro).
- Se a cobrança existe e está `paid`, muda pra `refunded` (status que já
  existia em `CHARGE_STATUSES`, usado hoje só pelo fluxo de cancelamento
  interno `PaymentService.refund_charge`) e loga `payments.charge_refunded`.
- Escopo deliberadamente contido: só atualiza o status da cobrança. NÃO mexe
  no estado da entrega (`deliveries.state`) — um estorno confirmado
  externamente pela Safe2Pay é um cenário distinto do cancelamento pelo
  nosso próprio fluxo (RN-004), e mudar o estado da entrega automaticamente
  merece decisão own separada caso apareça um caso de uso real.

## Backfill
`platform_charges` id 33 (a cobrança da entrega de teste 107, já estornada
pelo usuário antes desta correção) estava presa em `status=paid`. Corrigido
manualmente pra `refunded` pra refletir a realidade.

## Validado
Chamado `_process_event` diretamente com uma cobrança de teste sintética
(`transaction_id=999999999`, status inicial `paid`): log confirmou
`refunded: true`, status mudou pra `refunded` no banco, `payments.charge_refunded`
gravado. Registro de teste removido ao final.
