# CORRECAO-163 — Paginação /admin/equipes com FA icons

## Página
`http://localhost:4200/admin/equipes`

## Arquivo alterado
`apps/web/src/features/admin/equipes/equipes.page.ts`

## O que foi feito
A página já tinha paginação server-side implementada (limit/offset, PAGE_SIZE=20),
mas os controles de navegação não tinham FA icons, ficando fora do padrão visual
estabelecido nas páginas /equipe/entregadores e /equipe/entregas.

Mudanças:
- Importados `faChevronLeft` e `faChevronRight` de `@fortawesome/free-solid-svg-icons`
- Adicionadas propriedades `iconPrev` e `iconNext` à classe
- Template atualizado: botão "Anterior" com `<fa-icon [icon]="iconPrev">` antes do texto,
  botão "Próxima" com `<fa-icon [icon]="iconNext">` após o texto
- Adicionados `aria-label` nos botões de paginação
- Texto do contador atualizado de "X de Y" para "Página X de Y"

## Backend
Sem alteração — endpoint `/v1/admin/teams` já suportava `limit` e `offset`.
Não requer rebuild do container.
