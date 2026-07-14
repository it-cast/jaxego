# CORRECAO-251 — Bloqueio de troca de equipe pelo entregador

## Data
2026-07-13

## Pedido
"Na pagina de http://localhost:8100/entregador/perfil/editar-dados bloqueie a
possibilidade dele altera a equipe"

## Mudança
- Campo "Equipe" virou somente leitura (mesmo padrão de e-mail/telefone/CPF
  nessa tela — `input disabled` mostrando `profile().team_name`).
- Removido o `<select>` editável, o signal `teams()` e a dependência de
  `CourierCadastroService.listTeams()` (só existiam pra popular esse select).
- **Defesa em profundidade no backend**: `PATCH /v1/couriers/{id}/profile`
  (`update_courier_profile`) recebe um `dict` livre, sem schema — antes
  aceitava `team_id` de qualquer chamada. Removida essa branch, então mesmo
  uma chamada direta na API (bypassando o app) não muda mais a equipe por
  esse endpoint.
- `EntregadorService.updateProfile()` — tipo do payload não aceita mais
  `team_id`.

## Onde a equipe continua sendo definida
Só no cadastro (`CreateCourierBody.team_id`, `couriers/service.py`). Não há
endpoint de admin pra reatribuir equipe hoje — se precisar mudar a equipe de
um entregador depois do cadastro, é direto no banco por enquanto (fora de
escopo deste pedido).

## Build
- `docker compose exec api python -c "import app.couriers.router"` — limpo.
- `ng build app` — verde (avisos pré-existentes, não relacionados).
- API reiniciada.
