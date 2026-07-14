# CORRECAO-258 — Removido link do nome do entregador em /plataforma/pessoas

## Data
2026-07-14

## Pedido
"Em /plataforma/pessoas retire essa possibilidade de clicar no nome do
entregador e abrir uma página sobre ele. Essa página está dando erro, então
somente retire o link do nome do entregador."

## Causa
Não era navegação pra outra rota — o nome do entregador era um `<button>`
(`(click)="openBreakdown(item)"`) que abre um modal de "Score de {{nome}}"
na própria tela (`selectedCourier` signal). É esse modal que está dando erro
pro usuário.

## O que mudou
`apps/web/src/features/admin-plataforma/pessoas.page.html` — o `<button>`
clicável virou um `<td>{{ item.full_name }}}</td>` simples, sem clique.

## Não mexido (conforme pedido — "somente retire o link")
- `openBreakdown()` e o `selectedCourier` signal continuam no
  `pessoas.page.ts`, agora inalcançáveis (nenhum outro lugar chama
  `openBreakdown`) — código morto, não removido porque o pedido foi
  explicitamente só tirar o link.
- O bloco do modal ("Score de {{ courier.full_name }}") no HTML também
  continua — nunca mais abre, mas não apaguei.
- Não investiguei a causa do erro no modal em si (o pedido foi remover o
  acesso, não corrigir o breakdown).

## Build
`ng build web` — verde, sem erros novos.
