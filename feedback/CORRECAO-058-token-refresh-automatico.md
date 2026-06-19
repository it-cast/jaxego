# Correção 058 — Access token expirado não era renovado: erros após 15 minutos de uso

> **Classe:** COD · **Data:** 2026-06-19

---

## Arquivo afetado

- `packages/shared/src/core/auth/auth.interceptor.ts`

## Problema

O access token expira a cada 15 minutos. O interceptor HTTP anexava o token em todas as requisições, mas quando o backend retornava 401 (token expirado), o erro era simplesmente propagado. As telas mostravam "Não conseguimos carregar…" e só voltavam a funcionar após relogar manualmente.

O refresh token (cookie httpOnly, 30 dias) existia mas nunca era usado após o boot da aplicação.

## Correção

O interceptor agora trata 401:
1. Ao receber 401 (exceto em `/auth/refresh` e `/auth/login` para evitar loop), chama `AuthService.tryRestoreSession()` que faz `POST /v1/auth/refresh` com o cookie
2. Se o refresh retorna novo access token, repete a requisição original com o token novo
3. Se o refresh falha (cookie expirado/revogado), redireciona para `/entrar`
4. Requisições paralelas compartilham a mesma promise de refresh (evita múltiplos refreshes simultâneos)

## Resultado

O usuário fica logado por até 30 dias sem interrupção. O access token renova silenciosamente a cada 15 minutos sem que o usuário perceba.
