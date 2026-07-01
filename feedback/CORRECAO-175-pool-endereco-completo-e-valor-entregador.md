# CORRECAO-175 — Pool sem resposta: endereço completo de destino + valor do entregador

## Páginas afetadas
- `http://localhost:8100/entregador/sem-resposta`

## Problemas corrigidos

### 1. Endereço de destino incompleto
**Antes:** mostrava apenas o bairro de destino (`d.dropoff_neighborhood`).
**Depois:** mostra rua + número + bairro na linha de destino do timeline:
- `strong`: `d.dropoff_address`, `d.dropoff_number` (ex: "Rua das Flores, 123")
- `p.jx-pool__tl-sub`: bairro + distância em km concatenados (ex: "Centro · ~2,3 km")

**Motivo:** diferentemente da oferta individual (RN-013 — só bairro até aceitar), no pool
a entrega já passou por todos os entregadores elegíveis sem resposta. Expor o endereço
completo ajuda o entregador a decidir se vale aceitar antes de se deslocar.

### 2. Valor não aparecia
**Antes:** `value_cents=d.price_cents` — usava o preço estimado na criação da entrega, que
pode ser `None` (entrega criada sem preço fixado).
**Depois:** `value_cents=effective_price_cents(pricing_rows, dropoff_nbhd_id=..., distance_m=...)`
— usa a tabela de preço do próprio entregador para aquele bairro, igual ao que a oferta
individual já mostrava.

## Arquivos alterados

### Backend (apps/api)
- `app/dispatch/schemas.py` — `PoolItemOut`: adicionado `dropoff_address: str` e `dropoff_number: str | None`, atualizado docstring
- `app/dispatch/service.py` — `list_unanswered_pool()`: carrega `CourierPricingTable` do entregador, usa `effective_price_cents()`, popula `dropoff_address`/`dropoff_number`

### App entregador (apps/app)
- `src/features/entregador/sem-resposta/pool.models.ts` — `PoolItemOut` interface: adicionado `dropoff_address: string` e `dropoff_number: string | null`, atualizado comentário
- `src/features/entregador/sem-resposta/sem-resposta.page.ts` — template: destino mostra rua+número no `strong` e bairro+km no `p.jx-pool__tl-sub`

## Verificação
- `npx tsc -p apps/app/tsconfig.app.json --noEmit` — limpo
- `npx tsc -p apps/web/tsconfig.app.json --noEmit` — limpo
- `docker compose build api worker` — sucesso
