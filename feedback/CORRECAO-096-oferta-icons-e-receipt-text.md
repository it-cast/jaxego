# Correção 096 — Oferta: emojis trocados por fa-icons + receipt como texto

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/oferta/offer-sheet.component.ts`
- `apps/app/src/features/entregador/oferta/offer-sheet.component.scss`

## Correção

- Emojis substituídos por Font Awesome icons: `faStore` (coleta), `faLocationDot` (entrega), `faMoneyBill` (valor), `faRoute` (recebimento)
- "Você ganha R$..." redesenhado: card com fundo brand-wash, ícone de dinheiro à esquerda, label "Você ganha" + valor grande em brand color
- Badge de forma de pagamento removido — substituído por texto: "Forma de recebimento do cliente: **Dinheiro**" com ícone de rota
- Stops (coleta/entrega) agora com ícone + label na mesma linha
