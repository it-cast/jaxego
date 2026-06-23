# Correção 092 — Componente PageHeader compartilhado para o app

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `packages/shared/src/shared/components/page-header/page-header.component.ts` (criado)
- `packages/shared/src/shared/components/index.ts` — export adicionado
- `apps/app/src/features/entregador/perfil.page.ts` — usa PageHeader com title="Perfil"
- `apps/app/src/features/entregador/saldo/saldo.page.ts` + `.html` — usa PageHeader com title="Saldo"
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.ts` + `.html` — usa PageHeader com title="Bairros e precos"

## Problema

As páginas do app tinham headers inconsistentes — cada uma com seu próprio título e estilo.

## Correção

- Componente `jx-page-header` reutilizável com:
  - `title` (obrigatório) — texto centralizado
  - `backLink` (opcional) — se informado, exibe seta de voltar (faChevronLeft) no lado esquerdo como link
  - Layout: 3 colunas (back | título | spacer) com alinhamento centralizado, border-bottom, min-height 56px
- Aplicado nas 3 páginas: Perfil, Saldo, Bairros e preços (sem backLink nestas)
- Títulos antigos (h1 internos) removidos
