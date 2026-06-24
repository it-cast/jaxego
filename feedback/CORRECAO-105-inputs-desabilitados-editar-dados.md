# CORRECAO-105 — Campos readonly como inputs desabilitados

## O que mudou

### Frontend (apps/app)
- **editar-dados.page.ts**: Campos de e-mail, telefone e CPF trocados de `<div>` readonly para `<input disabled>` com mesmo estilo visual dos demais inputs. Fundo levemente cinza e texto muted para indicar que não são editáveis.

## Arquivos alterados
- apps/app/src/features/entregador/perfil/editar-dados.page.ts
