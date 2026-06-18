# Correção 007 — JWT com role incorreta para courier e merchant

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/api/app/auth/service.py`
- `apps/web/src/features/auth/login.page.ts`

## Problema

A função `_resolve_session_context` só verificava a tabela `area_admins`. Couriers e merchants sempre recebiam `role: "user"` no JWT, causando redirect errado para `/loja/painel` mesmo para entregadores.

## Correção

- Backend: `_resolve_session_context` agora verifica `couriers` e `merchant_users` quando não há membership em `area_admins`, retornando `"courier"` ou `"merchant"` respectivamente
- Frontend: redirect do login atualizado para tratar `"merchant"` e `admin_area:*` (com startsWith)
