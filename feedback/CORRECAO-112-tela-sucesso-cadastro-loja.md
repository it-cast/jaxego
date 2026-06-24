# CORRECAO-112 — Tela de sucesso após cadastro da loja

## O que mudou

### Frontend (apps/web)
- **cadastro-sucesso.page.ts**: Nova página `/loja/cadastro/sucesso` com:
  - Ícone de check verde (faCircleCheck)
  - Título "Cadastro realizado!"
  - Texto de boas-vindas e orientação
  - Botão pill laranja "Ir para o login" com ícone (faRightToBracket)
- **app.routes.ts**: Rota `loja/cadastro/sucesso` adicionada (antes de `loja/cadastro` para evitar captura)
- **cadastro.page.ts**: Após signup com sucesso, redireciona para `/loja/cadastro/sucesso` em vez de `/loja/inicio`

## Arquivos alterados
- apps/web/src/features/loja/cadastro/cadastro-sucesso.page.ts (novo)
- apps/web/src/app/app.routes.ts
- apps/web/src/features/loja/cadastro/cadastro.page.ts
