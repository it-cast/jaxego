# Correção 014 — Links de cadastro na tela de login apontando para rotas inexistentes

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivo afetado

- `apps/web/src/features/auth/login.page.html`

## Problema

Os links da tela de login usavam `/cadastro`, `/cadastro/loja` e `/cadastro/entregador`, que não existem no roteador. As rotas reais são `/loja/cadastro` e `/entregador/cadastro`. Qualquer clique nessas âncoras caia na tela de 404.

## Correção

Links corrigidos para `/loja/cadastro` e `/entregador/cadastro`. O link genérico "Criar conta" (que apontava para `/cadastro` sem destino definido) foi removido.
