# CORRECAO-195 — Redesign completo da tela entrega-detalhe

## Solicitação
Enriquecer a tela /loja/entregas/:id com dados completos de endereço, equipes acionadas, observações e itens. Mover status tree para horizontal no topo. Reduzir mapa para formato quadrado.

## Mudanças

### Backend — `apps/api/app/deliveries/schemas.py`
- `DeliveryOut`: adicionados `items_description`, `items_quantity`, `notes`, `pickup_address`, `pickup_neighborhood`, `dropoff_neighborhood_name`, `team_names`
- `CourierDeliveryOut`: adicionados `items_description`, `items_quantity`, `pickup_address`, `pickup_neighborhood`, `dropoff_neighborhood_name`, `team_names`

### Backend — `apps/api/app/deliveries/router.py`
- `_delivery_out()`: agora aceita `neighborhood_name` e `team_names` e os repassa ao schema
- Populado `items_description`, `items_quantity`, `notes`, `pickup_address`, `pickup_neighborhood`
- `get_delivery`: busca nome do bairro via `session.get(Neighborhood, ...)` e nomes das equipes via `select(Team.name).where(Team.id.in_(delivery.team_ids))`

### Frontend — `packages/shared/src/shared/models/delivery.models.ts`
- `DeliveryListItem`: adicionados campos opcionais `dropoff_address`, `dropoff_number`, `dropoff_complement`, `dropoff_reference`, `dropoff_neighborhood_name`, `pickup_address`, `pickup_neighborhood`, `items_description`, `items_quantity`, `notes`, `team_names`, `has_image`, `proof_method`

### Frontend — `apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.ts`
- Removido `TrackingTimelineComponent` (não usado mais no template)
- Adicionado `hSteps()` — gera passos da timeline horizontal inline
- Adicionado `fmtCents()` — formata valor em BRL
- Template redesenhado:
  - Header: ID + badge (mantido)
  - Banners contextuais: agendada / sem resposta
  - GIF de busca (mantido, quando CRIADA)
  - Timeline horizontal com dots ●/◉/○ e linhas entre passos (scrollável em mobile)
  - Grid 2 colunas (≥760px):
    - Esquerda: card Endereço (rua+numero, bairro, complemento, referência, coleta); card Itens/Obs; mapa quadrado (aspect-ratio 1/1)
    - Direita: card Destinatário (nome, telefone, entregador, equipes acionadas, valor, link); cancelar; fav/block; avaliação
