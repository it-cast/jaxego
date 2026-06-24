# CORRECAO-120 — Padronizar padding/margin em todas as telas da loja

## O que mudou

### Frontend (apps/web)
O shell (`loja-shell.component.ts`) já define `padding: var(--jx-space-5) var(--jx-space-4)` e `max-width: 860px` no `<main>`. Cada página tinha valores próprios de `max-width` (620, 640, 720, 760, 860, 980), `margin: 0 auto` e `padding` que conflitavam e causavam inconsistência visual. Removidos todos:

- **dashboard.page.scss**: Removido `max-width: 980px` e `margin: 0 auto`
- **entregas-list.page.scss**: Removido `max-width: 980px` e `margin: 0 auto`
- **nova-entrega.page.scss**: Removido `max-width: 620px` e `margin: 0 auto`
- **favoritos.page.scss**: Removido `max-width: 720px`, `margin: 0 auto` e `padding`
- **fatura.page.scss**: Removido `max-width: 760px`, `margin: 0 auto` e `padding`
- **plano.page.scss**: Removido `max-width: 860px`, `margin: auto` e `padding`
- **config.page.scss**: Removido `max-width: 640px` e `margin: 0 auto`
- **entrega-detalhe.page.scss**: Removido `padding` duplicado

## Arquivos alterados
- apps/web/src/features/loja/dashboard/dashboard.page.scss
- apps/web/src/features/loja/entregas/entregas-list.page.scss
- apps/web/src/features/loja/entregas/nova-entrega.page.scss
- apps/web/src/features/loja/favoritos/favoritos.page.scss
- apps/web/src/features/loja/financeiro/fatura.page.scss
- apps/web/src/features/loja/plano/plano.page.scss
- apps/web/src/features/loja/config/config.page.scss
- apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.scss
