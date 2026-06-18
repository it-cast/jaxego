# Correção 011 — Botão de sair ausente nos menus

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/core/auth/auth.service.ts`
- `apps/web/src/layouts/plataforma-shell.component.ts`
- `apps/web/src/layouts/admin-shell.component.ts`
- `apps/web/src/layouts/loja-shell.component.ts`
- `apps/web/src/layouts/entregador-shell.component.ts`

## Problema

Não havia forma de deslogar dentro da aplicação — nenhum shell tinha botão de saída.

## Correção

- `AuthService.logout()` atualizado para `async`: chama `POST /v1/auth/logout` (revoga o refresh token no backend) e limpa o access token em memória
- Botão "Sair" adicionado ao final de cada shell: sidebar inferior (plataforma e admin), topbar (loja), tab bar (entregador)
- Todos navegam para `/entrar` após logout
