# CORRECAO-123 — Entregador pode escolher equipe no cadastro

## O que mudou

### Backend (apps/api)
- **couriers/models.py**: Adicionado `team_id` (BigInteger, FK → teams.id, nullable, ON DELETE SET NULL)
- **alembic 0022**: Migration para adicionar coluna `team_id` com índice e FK
- **couriers/schemas.py**: `CourierSignupBody` agora aceita `team_id` (nullable)
- **couriers/service.py**: Signup salva `team_id` no Courier
- **couriers/router.py**: Novo endpoint público GET `/v1/couriers/teams?area_id=N` que lista equipes de uma área (para o select no cadastro)

### Frontend (apps/app)
- **cadastro.models.ts**: `CourierSignupRequest` agora inclui `team_id`
- **cadastro.service.ts**: Novo método `listTeams(areaId)` que chama o endpoint público
- **cadastro.page.ts**: Signal `teams`, campo `team_id` no form, `loadTeams` chamado ao trocar de área, `team_id` enviado no signup
- **cadastro.page.html**: Select de equipe aparece após selecionar a cidade, com opção "Individual (sem equipe)" como default

## Arquivos alterados
- apps/api/app/couriers/models.py
- apps/api/alembic/versions/0022_courier_team_id.py (novo)
- apps/api/app/couriers/schemas.py
- apps/api/app/couriers/service.py
- apps/api/app/couriers/router.py
- apps/app/src/features/entregador/cadastro/cadastro.models.ts
- apps/app/src/features/entregador/cadastro/cadastro.service.ts
- apps/app/src/features/entregador/cadastro/cadastro.page.ts
- apps/app/src/features/entregador/cadastro/cadastro.page.html
