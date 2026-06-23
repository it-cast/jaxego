# Correção 098 — Redesign da tela de entrega ativa

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts`

## Correção

- PageHeader adicionado com título "Entrega ativa" e back link para início
- Emojis (📦, 📝, 💵, 📱) substituídos por fa-icons: `faStore`, `faLocationDot`, `faBoxOpen`, `faNoteSticky`, `faHandHoldingDollar`, `faMobileScreen`
- Cards de coleta/entrega com ícone à esquerda no estilo da oferta
- Informações de pacote e observações com ícones inline
- Badge de recebimento trocado por texto "Forma de recebimento do cliente: **X**"
- Botões primário e secundário arredondados (pill, 999px)
- Botão primário laranja brand
- Modal de cobrança com fa-icons no lugar de emojis
