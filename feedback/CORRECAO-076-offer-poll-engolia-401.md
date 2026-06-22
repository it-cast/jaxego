# Correção 076 — Polling de ofertas engolia 401 e impedia refresh do token

> **Classe:** BUG · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/oferta/offer.service.ts`
- `apps/app/src/features/entregador/inicio.page.ts`

## Problema

O `OfferService.active()` tinha um `catch` genérico que engolia todos os erros, incluindo 401. Quando o access token expirava (a cada 15min), o interceptor HTTP não conseguia interceptar o 401 para fazer o refresh, porque o erro já tinha sido engolido pelo `catch` e convertido em `null`. O polling continuava rodando silenciosamente sem token válido, e as demais requisições falhavam — o app parava de funcionar sem deslogar o usuário.

## Correção

- `OfferService.active()`: re-throw de `HttpErrorResponse` com status 401 para que o interceptor possa capturar e fazer o refresh do token
- `pollOffer()` na página inicial: try/catch adicionado para que o re-throw do 401 não quebre o polling — o interceptor lida com o refresh automaticamente
