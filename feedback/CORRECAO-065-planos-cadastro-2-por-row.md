# Correção 065 — Cards de planos espremidos no cadastro da loja

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/features/loja/cadastro/cadastro.page.scss`

## Problema

No step 4 (Plano) do cadastro da loja, os 4 cards de planos ficavam todos na mesma row em telas ≥720px (`grid-template-columns: repeat(4, 1fr)`), dentro de um container de apenas 600px — ficavam espremidos e ilegíveis.

## Correção

- Removido o media query que forçava 4 colunas no desktop. Agora o grid é sempre `repeat(2, 1fr)` — 2 planos por row em qualquer tela.
