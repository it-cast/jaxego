# CORRECAO-193 — Remove mapa e adiciona complemento/referência na entrega ativa

## Solicitação
Retirar o mapa que aparecia em entregador/entrega-ativa e adicionar os novos campos de referência e complemento.

## Mudanças

### `apps/app/src/features/entregador/entregador.service.ts`
- Adicionado `dropoff_reference: string | null` à interface `CourierDelivery`

### `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts`
- Removido import e uso de `LiveMapComponent`
- Removido `computed` do import Angular (não era mais usado)
- Removidos computed signals `mapLat`, `mapLng` e método `mapAria()` (exclusivos do mapa)
- Removido bloco `@if (mapLat() !== null ...)` com `<jx-live-map>` do template
- Adicionados no card de destino (após endereço+número):
  - `dropoff_complement` exibido como `jx-active__muted`
  - `dropoff_reference` exibido com prefixo 📍 e estilo itálico (`.jx-active__reference`)
