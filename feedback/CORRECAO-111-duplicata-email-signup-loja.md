# CORRECAO-111 — Fix erro 500 ao cadastrar loja com e-mail já existente

## O que mudou

### Backend (apps/api)
- **merchants/service.py**: O `_assert_unique` verificava duplicatas na tabela `merchants`, mas o email vive na tabela `users` com constraint unique. Quando o email já existia como user (ex: entregador), o `session.flush()` falhava com `IntegrityError` não tratado, gerando 500. Adicionado try/except no flush do User para capturar `IntegrityError` e converter em `DuplicateAccountError` (que retorna mensagem amigável ao frontend).

## Arquivos alterados
- apps/api/app/merchants/service.py
