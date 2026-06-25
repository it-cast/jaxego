# CORRECAO-133 — Painel lateral de equipes com sanfona na nova entrega

## O que mudou

### Backend (apps/api)
- **deliveries/router.py**: Novo endpoint GET `/v1/deliveries/teams-online` que retorna equipes da área com seus entregadores online (nome, avaliação média, preço). Inclui grupo "Individual (sem equipe)" para entregadores sem equipe.

### Frontend (apps/web)
- **nova-entrega.page.html**: Layout redesenhado para 50/50 (form à esquerda, painel de equipes à direita). Removidos: select de equipe, frete estimado e warning de 0 couriers. Adicionado painel lateral com:
  - Título "Equipes disponíveis"
  - Cards sanfona por equipe com radio para seleção
  - Ao expandir: lista de entregadores online com avatar (inicial do nome), nome, avaliação e valor cobrado
  - Botão "Enviar para todos (geral)" com destaque quando selecionado
  - Responsivo: em telas < 860px vira coluna única
- **nova-entrega.page.ts**: Removidos signals de estimativa, imports de EstimateBox e WarnBanner. Adicionados: `teamsOnline`, `openTeamId`, `selectedTeamId`, `loadTeamsOnline`, `toggleTeam`, `selectTeam`. O `team_id` continua sendo enviado no submit.
- **nova-entrega.page.scss**: CSS do layout grid 50/50, cards sanfona, courier rows com avatar, sticky sidebar

## Arquivos alterados
- apps/api/app/deliveries/router.py
- apps/web/src/features/loja/entregas/nova-entrega.page.html
- apps/web/src/features/loja/entregas/nova-entrega.page.ts
- apps/web/src/features/loja/entregas/nova-entrega.page.scss
