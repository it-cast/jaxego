# Correção 021 — Tela de Ganhos do entregador era placeholder: implementação completa

> **Classe:** COD/PROC · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/app/src/features/entregador/ganhos.page.ts`
- `apps/app/src/features/entregador/ganhos.page.html` (criado)
- `apps/app/src/features/entregador/ganhos.page.scss` (criado)

## Problema

A tela de Ganhos (aba Ganhos) existia apenas como placeholder vazio — stub `<jx-empty-state>` onde o protótipo (`c-earnings`) especificava tela rica.

## Implementação

Tela completa espelhando `c-earnings` do protótipo:

- Cartão de saldo com gradiente escuro mostrando `balance_cents` (via `SaldoService.balance()`) e botão de saque PIX que navega para `/entregador/saldo`
- Aviso lateral (`jx-ganhos__direct-note`) explicando que pagamentos diretos não aparecem no saldo
- Tabela de extrato com `SaldoService.extract()`: colunas data, entrega (com badge PLATAFORMA) e valor em verde
- `formatCents` para exibição em BRL; estados de loading/error tratados com signals
