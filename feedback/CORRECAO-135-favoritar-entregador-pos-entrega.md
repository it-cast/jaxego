# CORRECAO-135 — Favoritar entregador após finalizar entrega

## O que mudou

### Frontend (apps/web)
- **entrega-detalhe.page.ts**: Botão "Favoritar entregador" / "Favoritado" aparece na tela de detalhe quando a entrega está FINALIZADA e tem courier_id. Ao carregar, verifica se o courier já é favorito. Toggle adiciona/remove favorito via FavoritosService.
- **entrega-detalhe.page.scss**: Estilo do botão de favoritar (borda, hover, estado ativo com cor brand)

## Arquivos alterados
- apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.ts
- apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.scss
