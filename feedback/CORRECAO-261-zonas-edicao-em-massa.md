# CORRECAO-261 — Edição/adição em massa de zonas com mapa compartilhado

## Data
2026-07-14

## Pedido
"Na rota /admin/zonas no add... exiba todos as zonas, no esquema de ir
clicando em + novo e abrir outro campo para digitar outro nome de zona. E no
mapa, ir exibindo as zonas que existem e as que forem sendo adicionado."
Complementado depois: "gostaria que ao ir para parte de adicionar já exiba
as já cadastradas também, para poder editar junto" — ou seja, não é só
mostrar as existentes como referência visual, é deixar EDITAR as existentes
na mesma tela, junto com as novas.

## Decisão tomada com o usuário
Perguntei como decidir em qual linha o próximo polígono desenhado deveria
entrar, já que várias linhas podem estar "abertas" ao mesmo tempo. Resposta:
uma linha ativa por vez — cada linha tem um botão "Desenhar"/"Redesenhar"
que arma o modo de desenho no mapa mirando aquela linha específica.

## Desenho

### `AreaMapComponent` (`admin-plataforma/area-map.component.ts`) ganhou um segundo modo
- **Single** (como já era): `[boundary]`/`(boundaryChange)`, um polígono
  editável — usado sem mudança nenhuma pelo "Editar zona" (edição de UMA
  zona por vez, fora do fluxo em massa).
- **Multi** (`[multiMode]=true`, novo): recebe `drafts` (array de `{id, name,
  boundary, color}`) + `activeDraftId`. Só o draft com esse id fica na
  camada editável do leaflet-draw (`drawnItems`); todos os outros — sejam
  zonas novas ainda não ativas, sejam zonas já cadastradas sendo mostradas
  junto — ficam numa camada de só-visual (`referenceItems`, sem interação),
  cada um com sua própria cor e um tooltip com o nome. Trocar de linha ativa
  redesenha tudo: o que estava ativo vira referência, o novo ativo fica
  editável.

### `zonas.page.ts` — "Adicionar" virou "editar/adicionar em massa"
- Ao abrir, monta uma linha pra CADA zona já cadastrada (nome + polígono
  pré-preenchidos, `zonaId` setado) + uma linha nova em branco no fim, já
  ativa pra desenho.
- "+ Nova zona" adiciona mais uma linha em branco e a torna ativa.
- Cada linha mostra um badge "Existente" ou "Nova", e "Alterada" se uma
  linha de zona existente teve nome ou polígono mexido (comparação com o
  valor original carregado).
- Botão de remover linha (🗑) **só tira da sessão de edição** — nunca chama
  delete de verdade. Apagar uma zona de verdade continua sendo só pelo botão
  de lixeira na lista (com confirmação e tratamento do 409 quando a zona
  está em uso), não mexi nisso.
- "Salvar alterações": só salva o que mudou de verdade —
  - Linha nova com nome+polígono → `POST` (criar).
  - Linha existente com nome OU polígono diferente do original → `PATCH`
    (atualizar). Linha existente sem nenhuma mudança é **ignorada** (não
    gera um PATCH à toa).
  - Se alguma falhar, só as que falharam continuam na tela pra tentar de
    novo (as que deram certo já saem, mensagem mostra quantas de cada tipo).

## Atualização (mesmo dia): removido o botão de editar da listagem
Como editar já é possível pelo "Adicionar" (agora um editor em massa que já
mostra as zonas existentes), o botão de lápis na lista virou redundante — o
usuário pediu pra tirar. Removido:
- O botão de editar (lápis) na tabela.
- O bloco inteiro do modo `'edit'` (formulário de uma zona só, com o mapa em
  modo single) — ficou 100% inalcançável sem o botão, então limpei junto:
  `showEdit()`, `save()` (a versão de uma zona só — `saveAllDrafts()`
  continua), `formName`, `formBoundary`, `editingId`, o ícone `iconEdit`, e
  o valor `'edit'` do `ViewMode`.
- O modo **single** do `AreaMapComponent` (`[boundary]`/`(boundaryChange)`)
  ficou sem nenhum consumidor agora — não removi do componente (é uma API
  pública razoável de manter), só não é mais usado por `zonas.page.ts`.

## Atualização (mesmo dia): não deixar remover linha de zona já existente
No modo de adicionar/editar em massa, o botão de remover linha (🗑) agora só
aparece nas linhas de zona **nova** (`zonaId === null`). Zonas já
cadastradas não têm mais esse botão na linha — a única forma de "sumir" com
uma delas dali é apagar de verdade pela lixeira da lista (fora do modo em
massa). Reforçado também dentro de `removeDraftRow()` (retorna sem fazer
nada se a linha tiver `zonaId`), não só escondendo o botão no template.

## Não mexido
- Apagar zona (lixeira na lista, com confirmação) continua igual.

## Validado
- `ng build web` — verde, sem erros novos.
- **Não testado ao vivo no navegador** — precisaria de login de admin de
  área, e não criei uma conta de teste sozinho (o classificador de
  segurança do ambiente bloqueou a tentativa de inserir uma conta de admin
  direto no banco, e concordo que essa não é uma ação pra eu tomar sem
  autorização explícita). Fica pendente de teste manual pelo usuário.

## Tech debt / pontos em aberto
- Sem paginação/filtro na lista de linhas do modo em massa — se a área
  tiver muitas zonas cadastradas, a lista fica longa (todas viram linha
  editável de uma vez). Não foi pedido, não implementei um limite.
- Comparação de "mudou" no polígono é via `JSON.stringify` (comparação
  estrutural simples, não uma normalização geométrica) — funciona bem pro
  caso real (o polígono só muda se o usuário mexer nele), mas tecnicamente
  dois GeoJSON com os mesmos pontos em ordem diferente contariam como
  "diferentes". Não é um cenário que acontece na prática aqui.
