# Correção 006 — Interceptor HTTP ausente: requisições saem sem token de autorização

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/core/auth/auth.interceptor.ts` (criado)
- `apps/web/src/app/app.config.ts`

## Problema

O `provideHttpClient` não tinha nenhum interceptor registrado. Todas as requisições HTTP do frontend saíam sem o header `Authorization: Bearer <token>`, resultando em 401/403 em todos os endpoints protegidos.

## Correção

Criado `authInterceptor` funcional que injeta o token em memória do `AuthService` em cada requisição. Registrado via `withInterceptors([authInterceptor])` no `app.config.ts`.
