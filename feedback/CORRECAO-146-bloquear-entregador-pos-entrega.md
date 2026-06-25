# CORRECAO-146 — Botão de bloquear entregador na entrega finalizada

## O que mudou

### Frontend (apps/web)
- **entrega-detalhe.page.ts**: Adicionado botão "Bloquear" ao lado do "Favoritar" na entrega finalizada. Os dois são mutuamente exclusivos (favoritar desabilita bloquear e vice-versa). Bloquear um favorito remove o favorito automaticamente (backend já fazia isso).
- **entrega-detalhe.page.scss**: Estilos dos botões em row (50/50), botão de bloquear com cor de erro
- **favoritos.service.ts**: Adicionado método `addBlock(courierId, reason?)` que faltava

## Arquivos alterados
- apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.ts
- apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.scss
- apps/web/src/features/loja/favoritos/favoritos.service.ts
