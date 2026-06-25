# CORRECAO-131 — Oferta expirada some automaticamente da tela

## O que mudou

### Frontend (apps/app)
- **inicio.page.ts**: O `pollOffer` parava de verificar quando já havia uma oferta no signal (`this.offer()`). Removida essa condição — agora o polling continua mesmo com oferta ativa. Quando o backend retorna `null` (oferta expirou/foi para outro entregador) e o signal tinha uma oferta, limpa o signal e a oferta some da tela automaticamente.

## Arquivos alterados
- apps/app/src/features/entregador/inicio.page.ts
