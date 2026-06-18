# Correção 020 — Áreas arquivadas na listagem, botões texto → ícones, modal de confirmação

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/features/admin-plataforma/areas.page.ts`
- `apps/web/src/features/admin-plataforma/areas.page.html`
- `apps/web/src/features/admin-plataforma/areas.page.scss`

## Problema

Áreas com `deleted_at` preenchido continuavam aparecendo na tabela. Botões de ação usavam texto ("Editar" e "Arquivar") em vez de ícones. Não havia modal de confirmação antes de arquivar — a ação era imediata.

## Correção

- `filteredAreas` (computed) agora filtra `deleted_at === null` — apenas áreas ativas são exibidas
- Botões substituídos por ícones Font Awesome: `faPenToSquare` (editar) e `faTrashCan` (arquivar)
- Modal de confirmação com backdrop: exibe nome da área, botão "Arquivar" (com loading "Arquivando…") e "Cancelar"; backdrop clicável cancela se não estiver processando
