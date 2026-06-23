# Correção 088 — Botão "Finalizar entrega" na comprovação + proof_method corrigido

> **Classe:** BUG · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/comprovacao/comprovacao.page.ts`
- `apps/app/src/features/entregador/comprovacao/comprovacao.page.scss`
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts`

## Problema 1 — Sem botão após anexar foto de entrega

Após o entregador tirar a foto de comprovação da entrega, a página ficava sem ação — não havia botão para finalizar nem navegação automática. Apenas coleta (pickup) e recusa navegavam; delivery ficava parado.

## Correção 1

- Após upload com sucesso da foto de delivery, exibe botão "Finalizar entrega" (pill brand)
- Ao clicar, navega para `/entregador/entrega/{id}/concluida`

## Problema 2 — Campo "nº do pedido" não aparecia na comprovação

Mesmo selecionando "Foto + nº do pedido" na criação da entrega, o campo de referência não aparecia na tela de comprovação do entregador.

## Correção 2

- O submit da nova entrega estava com `proof_method: 'photo'` hardcoded (ignorava a seleção do formulário)
- Corrigido para usar `this.proofMethod()` que reflete o valor real selecionado pelo lojista
- Com isso, o backend salva o `proof_method` correto, e a tela de comprovação exibe o campo de referência quando `photo_reference`
