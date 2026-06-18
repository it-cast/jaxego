# Correção 024 — Home do entregador sem cartão de ganhos, score e entregas recentes

> **Classe:** COD/PROC · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/app/src/features/entregador/inicio.page.ts`
- `apps/app/src/features/entregador/inicio.page.html` (criado — convertido de inline template)
- `apps/app/src/features/entregador/inicio.page.scss`

## Problema

A home do entregador (`c-home` do protótipo) mostrava apenas o header com toggle de disponibilidade e a máquina de estados de dispatch (offline/waiting/busy/offer-active). Faltavam os três blocos que o protótipo exibe acima do dispatch.

## Implementação

- Template inline convertido para `templateUrl: './inicio.page.html'`
- **Cartão de ganhos do dia:** gradiente escuro (`jx-neutral-800 → jx-neutral-700`), ganhos calculados do extrato filtrado por data de hoje, saldo p/ saque via `SaldoService.balance()`, link "Extrato →" para `/entregador/ganhos`
- **Mini-cartão de score:** nota total + badge de nível (bronze/prata/ouro/platina) via `GET /v1/couriers/{id}/score`, link "Por quê? →" para `/entregador/perfil`
- **Entregas recentes:** primeiras 3 entradas do extrato com badge PLATAFORMA e valor formatado
- Máquina de estados de dispatch permanece abaixo, sem alterações de comportamento
