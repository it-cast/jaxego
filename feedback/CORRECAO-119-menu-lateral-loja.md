# CORRECAO-119 — Menu lateral (sidebar) na loja

## O que mudou

### Frontend (apps/web)
- **loja-shell.component.ts**: Menu top substituído por sidebar lateral fixa com:
  - Ícones FA para cada item (Painel, Entregas, Favoritos, Faturas, Plano, Configurações)
  - Nome da loja exibido abaixo da marca
  - Link ativo com fundo brand-wash e cor brand
  - Botão "Sair da conta" no footer da sidebar
  - Responsivo: em telas < 860px a sidebar fica escondida e aparece via botão hamburger no topbar mobile, com overlay escuro
  - Em telas ≥ 860px a sidebar fica fixa à esquerda

## Arquivos alterados
- apps/web/src/layouts/loja-shell.component.ts
