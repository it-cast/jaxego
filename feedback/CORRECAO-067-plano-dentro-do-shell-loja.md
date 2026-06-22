# Correção 067 — Página de plano da loja sem menu/header

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/app/app.routes.ts`

## Problema

A rota `loja/plano` estava definida fora do `LojaShellComponent` (que renderiza o header/menu da loja). Por isso a página de plano aparecia sem navegação.

## Correção

- Movida a rota `loja/plano` para dentro dos `children` do shell da loja, junto com `painel`, `entregas`, etc. Agora herda o layout com header/menu.
