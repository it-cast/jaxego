# CORRECAO-164 — CRUD /admin/bairros padronizado como /admin/equipes

## Página
`http://localhost:4200/admin/bairros`

## Arquivos alterados
- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.ts` — reescrito
- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.html` — reescrito
- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.scss` — reescrito

## O que mudou

### Antes
- Formulário "Adicionar bairro" sempre visível no topo da página
- Sem header com título + botão de ação
- Sem busca/filtro
- Sem paginação
- Botão "Remover" vermelho bordado sem confirmação visual

### Depois (padrão /admin/equipes)
- **Header** com título "Bairros" + botão "+ Adicionar" (só no modo lista)
- **Modo toggle**: `list` | `create` via signal
- **Form card** aparece apenas ao clicar "+ Adicionar" (campos: nome + GeoJSON opcional)
- **Busca** client-side por nome do bairro com reset automático de página
- **Paginação** client-side 20 itens/página com FA icons (chevronLeft/Right)
- **Ações na linha**: botão de lixeira (fa-trash-can) com confirmação inline "Remover? ✓ ✕"
- **Feedback** via signal `msg` (ok/err) em vez de componente separado
- FA icons em todos os botões de ação

## Paginação
Client-side — o endpoint `/v1/neighborhoods` retorna lista plana sem total.
Não requer rebuild do container.

## Componentes removidos (não mais importados)
- `NeighborhoodRowComponent` — conteúdo inlineado no `ng-template #row`
- `ErrorStateComponent` — substituído por msg signal inline
