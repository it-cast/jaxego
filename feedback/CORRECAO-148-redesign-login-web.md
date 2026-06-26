# CORRECAO-148 — Redesign da tela de login web

## O que mudou

### Frontend (packages/shared)
- **login.page.html**: Layout split 50/50 — formulário à esquerda, painel visual à direita
  - Logo com ícone de escudo (faShieldHalved) em card laranja
  - Título "Bem-vindo de volta!" + subtítulo "Faça login para continuar"
  - Inputs com ícones FA (envelope para email, cadeado para senha)
  - Checkbox "Lembrar de mim"
  - Botão "Entrar" pill arredondado
  - "Não tem conta? Cadastrar minha loja" em linha
  - Painel direito com gradiente brand, ícone escudo, "Jaxegô" e descrição
  - Responsivo: em mobile o painel visual some
- **login.page.ts**: Adicionados ícones `faEnvelope`, `faLock`, `faShieldHalved`
- **login.page.scss**: CSS reescrito com layout split, inputs com ícone, botão pill, painel visual com gradiente

## Arquivos alterados
- packages/shared/src/shared/features/auth/login.page.html
- packages/shared/src/shared/features/auth/login.page.ts
- packages/shared/src/shared/features/auth/login.page.scss
