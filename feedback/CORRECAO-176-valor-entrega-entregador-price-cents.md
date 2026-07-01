# CORRECAO-176 — Valor errado na lista de entregas do entregador

## Páginas afetadas
- `http://localhost:8100/entregador/entregas`
- `http://localhost:8100/entregador/concluida` (mesmo bug)

## Problema
O backend envia o campo `price_cents` (valor da corrida do entregador) mas o
modelo TypeScript do frontend declarava `estimate_min_cents` e `estimate_max_cents`.
Por ser um campo inexistente na resposta JSON, `estimate_min_cents` ficava `null`
e o fallback `?? d.fee_cents` usava a taxa da plataforma (ex: R$ 2,00) em vez
do valor configurado pelo entregador para o bairro (ex: R$ 3,00).

## Causa raiz
Divergência de nomenclatura: `price_cents` no backend ↔ `estimate_min_cents` no front.

## Correção
- `entregador.service.ts` — renomeado `estimate_min_cents`/`estimate_max_cents` para
  `price_cents` em ambas as interfaces: `CourierDelivery` e `CourierDeliveryListItem`
- `entregas.page.ts` — template atualizado: `d.estimate_min_cents ?? d.fee_cents`
  → `d.price_cents ?? d.fee_cents`
- `concluida/concluida.page.ts` — mesma substituição na tela de entrega concluída

## Verificação
- `npx tsc -p apps/app/tsconfig.app.json --noEmit` — limpo
