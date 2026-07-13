# CORRECAO-231 — Logout e 401 redirecionam para o login da superfície

## Data
2026-07-10

## Problema
Após a CORRECAO-230 (logins por perfil), o logout e a expiração de sessão
sempre jogavam para `/entrar` (login da loja), mesmo quando o usuário estava
na superfície de equipe, admin ou plataforma.

## Mudanças
- `packages/shared/src/core/auth/auth.service.ts`: novo helper
  `loginPathForUrl(url)` — mapeia prefixo da URL para o login da superfície
  (`/equipe*` → `/equipe/entrar`, `/admin*` → `/admin/entrar`,
  `/plataforma*` → `/plataforma/entrar`, default `/entrar`).
- `auth.guard.ts`: usa `state.url` para redirecionar não-autenticados ao login
  da superfície que tentaram acessar.
- `auth.interceptor.ts`: no 401 sem refresh possível, redireciona pelo
  `router.url` atual.
- Shells: `equipe-shell`, `admin-shell` e `plataforma-shell` navegam para o
  próprio login no logout. `loja-shell` continua em `/entrar` (é o login dela).
