# CORRECAO-126 — Direcionar entrega para equipe específica

## O que mudou

### Backend (apps/api)
- **deliveries/models.py**: Adicionado `team_id` (BigInteger, FK → teams.id, nullable, ON DELETE SET NULL)
- **alembic 0023**: Migration para adicionar coluna `team_id` em deliveries
- **deliveries/schemas.py**: `CreateDeliveryBody` agora aceita `team_id` (nullable)
- **deliveries/service.py**: Criação da entrega salva `team_id`
- **dispatch/cascade.py**: `build_candidates` aceita `team_id`. Quando não é null, filtra couriers pela equipe
- **workers/dispatch.py**: Passa `delivery.team_id` ao `build_candidates`

### Frontend (apps/web)
- **delivery.models.ts**: `CreateDeliveryRequest` agora inclui `team_id`
- **nova-entrega.page.ts**: Signal `teams`, campo `team_id` no form, `loadTeams` no constructor, `team_id` enviado no submit
- **nova-entrega.page.html**: Select "Direcionar para" com opção "Todos (geral)" + equipes da área. Só aparece se a área tem equipes cadastradas

## Arquivos alterados
- apps/api/app/deliveries/models.py
- apps/api/alembic/versions/0023_delivery_team_id.py (novo)
- apps/api/app/deliveries/schemas.py
- apps/api/app/deliveries/service.py
- apps/api/app/dispatch/cascade.py
- apps/api/app/workers/dispatch.py
- packages/shared/src/shared/models/delivery.models.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.html
