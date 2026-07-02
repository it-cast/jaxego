# CORRECAO-182 — Zonas: estilo igual ao de Equipes

## Arquivo modificado
- `apps/web/src/features/admin/zonas/zonas.page.ts`: reescrito com o mesmo CSS/estrutura de `equipes.page.ts`
  — `display: flex; flex-direction: column; gap` sem max-width (100% da tela)
  — header com `font-family: var(--jx-font-display); font-size: var(--jx-text-2xl)`
  — form card com `border-radius: var(--jx-radius-xl); padding: var(--jx-space-5)`
  — labels uppercase/muted, inputs min-height 44px, action buttons 36×36
  — coluna "Polígono" com badge Com/Sem
  — filtro de busca, paginação
