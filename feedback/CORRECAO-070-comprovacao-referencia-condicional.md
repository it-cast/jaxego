# Correção 070 — Campo "Número do pedido" exibido mesmo quando proof_method é só foto

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/comprovacao/comprovacao.page.ts`

## Problema

Na tela de comprovação do app do entregador, o campo "Número do pedido (pergunte ao destinatário)" aparecia sempre que o `kind` era `delivery`, independente do `proof_method` configurado pela loja na criação da entrega. Se a loja escolheu apenas "Foto na entrega" (`photo`), o campo não deveria aparecer.

## Correção

- Adicionado signal `proofMethod` que carrega o `proof_method` da entrega via `EntregadorService.getDelivery()`
- Novo método `needsReference()`: retorna `true` apenas quando `kind === 'delivery'` E `proofMethod === 'photo_reference'`
- Template condiciona a seção de referência com `needsReference()` em vez de `paymentNeeded()`
- `paymentNeeded()` mantido para a seção de confirmação de pagamento direto (que é independente do proof_method)
