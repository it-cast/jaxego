# CORRECAO-194 — Adiciona nome do bairro na linha de endereço da entrega ativa

## Solicitação
Incluir o nome do bairro junto com a rua e número na seção de Entrega em entregador/entrega-ativa.

## Mudanças

### `apps/api/app/deliveries/schemas.py`
- `CourierDeliveryOut`: adicionado `dropoff_neighborhood_name: str | None = None`

### `apps/api/app/couriers/router.py`
- `_courier_delivery_out()`: adicionado parâmetro `dropoff_neighborhood_name` e passagem para schema
- `get_active_delivery`: adicionado lookup `nbhd = await session.get(Neighborhood, delivery.dropoff_neighborhood_id)` e `dropoff_neighborhood_name=nbhd.name if nbhd else None`
- `get_delivery`: mesma lógica de lookup de bairro

### `apps/app/src/features/entregador/entregador.service.ts`
- Interface `CourierDelivery`: adicionado `dropoff_neighborhood_name: string | null`

### `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts`
- Template: linha de endereço agora exibe `rua, número, bairro` na mesma `<p>`:
  ```
  {{ dropoff_address }}@if (dropoff_number) {, {{ dropoff_number }}}@if (dropoff_neighborhood_name) {, {{ dropoff_neighborhood_name }}}
  ```
