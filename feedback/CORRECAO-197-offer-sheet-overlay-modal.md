---
classe: bugfix-ui
data: 2026-07-06
arquivos_afetados:
  - apps/app/src/features/entregador/oferta/offer-sheet.component.ts
  - apps/app/src/features/entregador/oferta/offer-sheet.component.scss
---

## Problema
O modal de oferta aparecia abaixo do tab bar do entregador porque `.jx-offer-sheet` não tinha `position: fixed` — ele fluía no DOM após o `<nav>` de abas.

## Implementação
- Adicionado wrapper `.jx-offer-overlay` em volta de `.jx-offer-sheet` no template
- `.jx-offer-overlay`: `position: fixed; inset: 0; z-index: 9999; display: flex; align-items: flex-end` com backdrop `rgba(0,0,0,0.55)`
- Animação `jx-backdrop-in` (fade-in) no overlay; sheet manteve o slide-up existente
- `@media (prefers-reduced-motion)` desativa animação do backdrop
- O host do shell usa `display: contents` — não cria box de layout, então `position: fixed` ancora diretamente no viewport acima de tudo
