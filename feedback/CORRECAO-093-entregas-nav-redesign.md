# Correção 093 — Aba "Entregas" no menu nav + redesign da lista

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/layouts/entregador-shell.component.ts` — nova aba "Entregas" com ícone `faBoxOpen`
- `apps/app/src/features/entregador/entregas.page.ts` — redesign completo

## Problema

A página de entregas não tinha ícone no menu nav (só era acessível por rota direta) e o layout era básico com cards genéricos.

## Correção

- Aba "Entregas" adicionada ao nav bar entre "Ganhos" e "Bairros" com ícone de caixa aberta
- Lista redesenhada no estilo do mockup: ícone circular com emoji por estado, nome do estado em negrito, data + ID da entrega, valor à direita
- PageHeader com título "Entregas"
- Itens ativos (ACEITA/COLETADA) são clicáveis e navegam para entrega ativa
