# Correção 081 — Login do app entregador separado do shared com novo design

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/auth/login.page.ts` (criado)
- `apps/app/src/features/auth/login.page.html` (criado)
- `apps/app/src/features/auth/login.page.scss` (criado)
- `apps/app/src/app/app.routes.ts` — rota aponta para `AppLoginPage` local em vez do shared
- `apps/app/public/login-hero.png` (criado)
- `packages/shared/src/shared/features/auth/login.page.html` — restaurado ao original
- `packages/shared/src/shared/features/auth/login.page.scss` — restaurado ao original

## Problema

O login era compartilhado entre web (loja/admin) e app (entregador). Ao redesenhar o login do app, alterava também o login da loja.

## Correção

- Criado `AppLoginPage` próprio em `apps/app/src/features/auth/` com o novo design
- Shared `LoginPage` restaurado ao original — web continua inalterado
- Novo design do app: hero image no topo (foto do entregador), inputs pill-shaped, "Bem-vindo!" como título, botão arredondado, CTA "Quer entregar? Cadastre-se"
- Rota `/entrar` do app agora aponta para `AppLoginPage`
