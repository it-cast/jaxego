# CORRECAO-113 — Botão "Voltar" no cadastro da loja

## O que mudou

### Frontend (apps/web)
- **cadastro.page.html**: Botão "Continuar" agora fica em uma row com "Voltar" (50/50) a partir do step 2. No step 1, só "Continuar" aparece (largura total).
- **cadastro.page.scss**: Estilos para `.jx-cadastro__actions` (flex row), `.jx-cadastro__back` (borda cinza, transparente) e `.jx-cadastro__submit` agora com `flex: 1`.

## Arquivos alterados
- apps/web/src/features/loja/cadastro/cadastro.page.html
- apps/web/src/features/loja/cadastro/cadastro.page.scss
