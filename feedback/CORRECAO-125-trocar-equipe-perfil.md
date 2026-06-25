# CORRECAO-125 — Trocar equipe na tela de editar dados do entregador

## O que mudou

### Backend (apps/api)
- **couriers/schemas.py**: `CourierProfileOut` agora inclui `team_id` e `team_name`
- **couriers/router.py**: GET profile busca o nome da equipe se `team_id` não for null. PATCH profile aceita `team_id` (null para sair da equipe)

### Frontend (apps/app)
- **entregador.service.ts**: Interface `CourierProfile` agora inclui `team_id` e `team_name`. `updateProfile` aceita `team_id`
- **editar-dados.page.ts**: Select de equipe adicionado entre CPF e botão de senha. Carrega equipes da área via `cadastroSvc.listTeams`. Ao salvar, envia `team_id` (null = individual)

## Arquivos alterados
- apps/api/app/couriers/schemas.py
- apps/api/app/couriers/router.py
- apps/app/src/features/entregador/entregador.service.ts
- apps/app/src/features/entregador/perfil/editar-dados.page.ts
