# Correção 033 — Removido toggle de tema escuro do app do entregador

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivo afetado

- `apps/app/src/features/entregador/perfil.page.ts`

## Problema

A tela de Perfil do entregador tinha um toggle "Tema escuro" (`<jx-theme-toggle />`) que não é necessário no app mobile neste momento.

## Correção

- Removido import de `ThemeToggleComponent`
- Removido `<jx-theme-toggle />` do template
- Removido estilo `.jx-perfil__theme`
