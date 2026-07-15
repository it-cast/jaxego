# CORRECAO-263 — Ocultar tela de saldo do app do entregador

## Data
2026-07-15

## Pedido
"Vamos ocultar a tela http://localhost:8100/entregador/saldo do app,
retirando do menu tbm"

## O que foi feito
Removida a rota e todos os pontos de navegação pra ela, sem apagar o
componente/service (`saldo.page.ts`, `saldo.service.ts` e specs continuam no
repo, só ficaram órfãos):

1. **Rota** (`apps/app/src/app/app.routes.ts`) — removida a entry `path:
   'saldo'` do bloco filho de `entregador`. Acesso direto pela URL agora dá
   404 de rota (comportamento padrão do router).
2. **Tab bar** (`apps/app/src/layouts/entregador-shell.component.ts`) —
   removido o tab "Ganhos" que linkava pra lá. Removido também o ícone
   `faMoneyBill`/`iconGanhos`, que ficou sem uso.
3. **Card da tela inicial** (`apps/app/src/features/entregador/inicio.page.ts`)
   — removido o botão "Ver extrato" (chamava `goSaldo()`, que navegava pra
   `/entregador/saldo`) e o método `goSaldo()` em si, que ficou sem uso.
   Mantido o texto "Saldo: R$ X" que já aparecia no mesmo card — é só
   informativo, não navega pra lugar nenhum, e não foi pedido pra remover.

## Validado
- `ng build app` — verde, sem erros. Nenhum warning novo introduzido.
- Confirmado que o chunk lazy `saldo-page` não aparece mais na lista de
  lazy chunks do build (a rota lazy-loaded não é mais registrada).
- `grep` por `EntregadorSaldoPage` / `/entregador/saldo` no `src/` só retorna
  o próprio arquivo do componente e seu spec — nenhuma referência ativa
  sobrou em rotas, menus ou botões.

## Tech debt / pontos em aberto
- `saldo.page.ts`, `saldo.service.ts` e os specs ficaram como código morto
  no repo (não deletei, seguindo o padrão já usado noutras remoções de link
  nesta sessão — só tirar o acesso, não apagar a implementação). Se algum
  dia vira definitivo, dá pra apagar os 4 arquivos junto.
