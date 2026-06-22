# Correção 083 — Botão "Entrando..." com spinner no login do app

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/auth/login.page.html`
- `apps/app/src/features/auth/login.page.scss`

## Problema

Ao clicar em "Entrar", um skeleton loader avulso aparecia abaixo do botão, sem relação visual clara com a ação.

## Correção

- Removido o `jx-loading-skeleton` avulso abaixo do botão
- Botão agora mostra "Entrando..." com spinner CSS circular quando `loading()` é true
- Botão fica `disabled` durante o loading
- Spinner usa `border` CSS com animação `rotate` (sem dependência de componente externo)
