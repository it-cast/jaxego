# CORRECAO-255 — Removida validação de entregador do painel do admin da área

## Data
2026-07-14

## Pedido
"Pode remover o 'Filas que precisam de você' / 'Validações de entregador
aguardando' do admin, já que quem faz esse papel agora é o admin do time."

## Confirmado antes de mexer
`/admin/entregadores` (o link daquele item) **não tem rota registrada** em
`app.routes.ts` sob `path: 'admin'` — já era um link morto. A validação de
KYC do entregador é feita pelo admin do time (`/equipe/entregadores`,
`EquipeEntregadoresPage`, rota viva).

Perguntei se era pra remover só essa linha ou o card inteiro (ele também
lista Disputas de pagamento direto e Recursos de suspensão, que continuam
sendo papel do admin da área, com rota viva em `/admin/disputas`) — resposta:
só a linha.

## O que mudou
`apps/web/src/features/admin/inicio.page.ts`:
- Removida a entrada "Validações de entregador aguardando" do array
  `queues` (inicial e do `ngOnInit`).
- Removida a injeção de `AdminKycService` e a chamada
  `kyc.listCouriers('pending_kyc')` (só existiam pra essa linha).
- Card "Filas que precisam de você" continua no painel, agora só com
  Disputas de pagamento direto e Recursos de suspensão.

## Achado incidental (não mexido)
`admin/entregadores/entregadores-list.page.ts` e
`admin/governanca/entregador-detalhe.page.ts` também não têm rota
registrada — código morto órfão da mesma mudança de papéis. Não apaguei
(fora do escopo do pedido), só registro aqui.

## Build
`ng build web` — verde.
