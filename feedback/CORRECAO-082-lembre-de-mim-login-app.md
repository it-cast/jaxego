# Correção 082 — Checkbox "Lembre de mim" no login do app entregador

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/auth/login.page.ts`
- `apps/app/src/features/auth/login.page.html`
- `apps/app/src/features/auth/login.page.scss`

## Problema

O entregador precisava digitar email e senha toda vez que abria o app ou era deslogado.

## Correção

- Checkbox "Lembre de mim" adicionado abaixo dos campos de login
- Ao logar com sucesso com o checkbox marcado, email e senha são salvos no `sessionStorage` (`jx-remember-login`)
- Na próxima abertura do login, os campos são pré-preenchidos automaticamente
- Se o checkbox estiver desmarcado, os dados salvos são removidos do `sessionStorage`
- `FormsModule` adicionado aos imports para suportar `ngModel` standalone
