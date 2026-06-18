# Correção 004 — Redirecionamento após login sempre volta para /entrar

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/features/auth/login.page.ts`
- `apps/web/src/core/auth/auth.service.ts`

## Problema

Após login bem-sucedido, o código navegava para `/` que redireciona incondicionalmente para `/entrar` — o usuário ficava preso na tela de login mesmo autenticado.

## Correção

O `AuthService` agora decodifica o JWT para expor a `role` do usuário. O `LoginPage` usa essa role para redirecionar para a área correta após login:

- `admin_plataforma` → `/plataforma/visao-geral`
- `admin_area` → `/admin/inicio`
- `courier` → `/entregador/inicio`
- default (merchant) → `/loja/painel`
