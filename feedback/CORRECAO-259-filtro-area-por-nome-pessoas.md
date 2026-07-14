# CORRECAO-259 — Filtro de área por nome em /plataforma/pessoas

## Data
2026-07-14

## Pedido
"O filtro de área está pelo ID, coloque pelo nome da área."

## O que mudou
`apps/web/src/features/admin-plataforma/pessoas.page.ts` + `.html`:
- Campo era um `<input type="number">` livre — o admin precisava saber o ID
  numérico da área de cor.
- Virou um `<select>` populado com `PlatformAdminService.listAreas()`
  (endpoint que a própria tela de áreas já usa), ordenado alfabeticamente
  (`localeCompare` pt-BR). Opção "Todas as áreas" no topo.
- O valor enviado pro backend continua sendo o `area_id` numérico
  (`[ngValue]="a.id"`) — só a representação na tela mudou, o contrato com a
  API (`searchCouriers`/`searchMerchants({ areaId })`) não mudou.
- Áreas carregadas em paralelo com a busca inicial (`Promise.all` no
  `ngOnInit`), falha ao carregar áreas não quebra a tela (select fica vazio,
  só com "Todas as áreas").

## CSS
`.jx-plat-people__input--num` (modificador do input numérico antigo) ficou
morto — removido, substituído por `select.jx-plat-people__input { min-width:
180px }` (nomes de área são mais longos que um ID de 1-3 dígitos).

## Build
`ng build web` — verde.
