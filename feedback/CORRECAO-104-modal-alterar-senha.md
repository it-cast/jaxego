# CORRECAO-104 — Modal de alteração de senha no perfil do entregador

## O que mudou

### Frontend (apps/app)
- **editar-dados.page.ts**: Campo inline de senha removido. Adicionado botão "Alterar senha" (ícone cadeado) que abre modal bottom-sheet com:
  - Senha atual (com toggle eye via `<fa-icon>`)
  - Nova senha (com toggle eye via `<fa-icon>`)
  - Confirmar nova senha (com toggle eye via `<fa-icon>`)
  - Validação: senha atual obrigatória, senhas devem coincidir
  - Após sucesso, modal fecha automaticamente em 1.5s
  - Mensagem de erro: "Senha atual incorreta."
- **entregador.service.ts**: Tipo de `updateProfile` agora aceita `current_password`
- Ícones usam `@fortawesome/angular-fontawesome` (`<fa-icon>`) — padrão do projeto (não `<i class="fa">`)
- Validação de mínimo 10 caracteres removida (frontend e backend)

### Backend (apps/api)
- **couriers/router.py**: Endpoint PATCH `/{courier_id}/profile` agora exige `current_password` para alterar senha. Verifica hash com `verify_password` antes de aceitar a troca. Retorna 400 "Senha atual incorreta" se não bater.

## Arquivos alterados
- apps/app/src/features/entregador/perfil/editar-dados.page.ts
- apps/app/src/features/entregador/entregador.service.ts
- apps/api/app/couriers/router.py
