# CORRECAO-134 — Múltiplas equipes por entrega, equipe obrigatória para entregador

## O que mudou

### Backend (apps/api)
- **deliveries/models.py**: `team_id` (FK) substituído por `team_ids` (JSON array)
- **alembic 0024**: Migration drop FK + coluna `team_id`, add coluna `team_ids` JSON
- **deliveries/schemas.py**: `CreateDeliveryBody.team_ids` é `list[int]` com `min_length=1`
- **deliveries/service.py**: Salva `team_ids` na entrega
- **dispatch/cascade.py**: `team_ids` (lista) → filtra `Courier.team_id.in_(team_ids)`
- **deliveries/estimate.py**: Idem
- **workers/dispatch.py**: Passa `delivery.team_ids`
- **deliveries/router.py**: teams-online removeu grupo "Individual"
- **couriers/models.py**: `team_id` agora NOT NULL (todo entregador pertence a uma equipe)
- **couriers/schemas.py**: `CourierSignupBody.team_id` obrigatório (`Field(gt=0)`), `CourierProfileOut.team_id` não nullable

### Frontend (apps/app)
- **cadastro.page.html**: Select de equipe obrigatório, sem opção "Individual"
- **cadastro.models.ts**: `team_id` obrigatório (number, não nullable)
- **cadastro.page.ts**: Validator required no `team_id`
- **editar-dados.page.ts**: Select de equipe sem opção "Individual"

### Frontend (apps/web)
- **delivery.models.ts**: `team_ids: number[]` (obrigatório)
- **nova-entrega.page.html**: Checkboxes em vez de radio, sem "Enviar para todos"
- **nova-entrega.page.ts**: `selectedTeamIds` como Set, `canSubmit` exige ≥1 equipe
- **nova-entrega.page.scss**: Estilo de checkbox e card selecionado

## Arquivos alterados
- apps/api/app/deliveries/models.py
- apps/api/alembic/versions/0024_delivery_team_ids_json.py (novo)
- apps/api/app/deliveries/schemas.py
- apps/api/app/deliveries/service.py
- apps/api/app/deliveries/estimate.py
- apps/api/app/dispatch/cascade.py
- apps/api/app/workers/dispatch.py
- apps/api/app/deliveries/router.py
- apps/api/app/couriers/models.py
- apps/api/app/couriers/schemas.py
- packages/shared/src/shared/models/delivery.models.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.html
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.scss
- apps/app/src/features/entregador/cadastro/cadastro.page.html
- apps/app/src/features/entregador/cadastro/cadastro.models.ts
- apps/app/src/features/entregador/cadastro/cadastro.page.ts
- apps/app/src/features/entregador/perfil/editar-dados.page.ts
