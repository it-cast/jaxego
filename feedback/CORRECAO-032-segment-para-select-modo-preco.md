# Correção 032 — Seletor de modo de preço trocado de segment buttons para select

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.html`
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.scss`

## Problema

O seletor de modo de precificação ("Por bairro" / "Por km") usava dois botões segment side-by-side, dando a impressão de que ambos podiam ser selecionados simultaneamente. Na prática, é uma escolha exclusiva — salvar num modo substitui o outro.

## Correção

Segment buttons substituídos por um `<select>` com duas opções ("Preço por bairro" / "Preço por km"), label "Como você cobra". Deixa claro que é uma escolha única. Estilos dos botões segment removidos; adicionados estilos do select (min-height 44px, border, border-radius).
