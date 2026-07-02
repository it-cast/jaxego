# CORRECAO-190 — Equipes online: remover rebusca por bairro, adicionar polling

## Problema
`nova-entrega.page.ts` rebuscava `/v1/deliveries/teams-online?dropoff_neighborhood_id=X` toda vez que o usuário mudava o bairro de destino. Com a migração para zonas, o bairro não determina mais quais equipes atendem — a rebusca ficou sem sentido e gerava requests desnecessários.

## Solução
- Removido `valueChanges.subscribe` no `dropoff_neighborhood_id` que disparava `loadTeamsOnline`
- Removido parâmetro `neighborhoodId` de `loadTeamsOnline` e o `params` condicional
- Mantida a busca inicial ao entrar na página (constructor)
- Adicionado polling de 60s via `interval(60_000).pipe(takeUntilDestroyed(destroyRef))` — atualiza automaticamente a lista de entregadores online sem rebusca por bairro
