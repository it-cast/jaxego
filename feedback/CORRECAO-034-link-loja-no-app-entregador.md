# Correção 034 — Link "Cadastrar minha loja" aparecia na tela de login do app do entregador

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/app/app.routes.ts`
- `packages/shared/src/shared/features/auth/login.page.ts`
- `packages/shared/src/shared/features/auth/login.page.html`

## Problema

A tela de login é compartilhada entre `apps/web` e `apps/app`. No app do entregador, aparecia o link "Cadastrar minha loja →" que leva a `/loja/cadastro` — rota que não existe no app (a loja se cadastra pelo web). Clicar nesse link levava a 404.

## Correção

- Rota de login no `apps/app` agora passa `data: { surface: 'app' }`
- Login page lê `ActivatedRoute.snapshot.data['surface']` e expõe `isApp`
- Template condiciona: `@if (!isApp)` para o link da loja — só aparece no web
- O link "Quero entregar →" continua visível em ambos
