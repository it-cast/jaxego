# Correção 008 — Sessão perdida ao recarregar a página (F5)

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/core/auth/auth.service.ts`
- `apps/web/src/app/app.config.ts`

## Problema

O access token ficava apenas em memória. Ao recarregar a página, o Angular reiniciava e o token era perdido — o authGuard redirecionava para `/entrar` mesmo com sessão válida. O refresh token existia no cookie httpOnly mas nunca era usado para restaurar a sessão.

## Correção

Adicionado método `tryRestoreSession()` no `AuthService` que chama `POST /v1/auth/refresh` com `withCredentials: true` ao inicializar. Registrado via `APP_INITIALIZER` no `app.config.ts` para executar antes das rotas serem resolvidas.
