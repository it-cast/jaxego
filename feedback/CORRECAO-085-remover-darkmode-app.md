# Correção 085 — Modo escuro removido do app do entregador

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/index.html`

## Problema

O app do entregador detectava `prefers-color-scheme: dark` do sistema e aplicava modo escuro automaticamente, ou permitia salvar via `localStorage`.

## Correção

- Script anti-FOUC simplificado para sempre setar `data-theme="light"`
- Removida detecção de `prefers-color-scheme` e leitura de `localStorage('jx-theme')`
- App sempre inicia em modo claro
