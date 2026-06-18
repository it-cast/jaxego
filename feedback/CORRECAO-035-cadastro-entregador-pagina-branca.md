# Correção 035 — Link "Quero entregar" levava a página em branco no app

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `packages/shared/src/shared/features/auth/login.page.html`
- `packages/shared/src/shared/features/auth/login.page.ts`

## Problema

O link "Quero entregar →" na tela de login usava `href="/entregador/cadastro"` (navegação HTML nativa), que causa um reload completo da SPA. No contexto do app standalone com `AppComponent` local, o reload não re-inicializava o Angular corretamente, resultando em página branca.

## Correção

- Links `href` trocados por `routerLink` (navegação SPA sem reload)
- `RouterLink` adicionado aos imports do `LoginPage`
- Afeta tanto o link da loja (`/loja/cadastro`) quanto o do entregador (`/entregador/cadastro`)
