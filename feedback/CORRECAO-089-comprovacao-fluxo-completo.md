# Correção 089 — Fluxo de comprovação reescrito: foto + validação + finalizar

> **Classe:** BUG · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/comprovacao/comprovacao.page.ts` (reescrito)
- `apps/app/src/features/entregador/comprovacao/comprovacao.page.scss`

## Problemas

1. A foto era enviada ao backend imediatamente ao ser capturada, finalizando a entrega antes do entregador confirmar
2. O campo de número do pedido não validava se estava correto — apenas salvava sem feedback
3. Não havia botão "Finalizar entrega" — a página ficava sem ação após a foto

## Correção

Fluxo reescrito em 3 etapas:

1. **Captura da foto**: salva localmente com preview — NÃO envia ao backend ainda (apenas para pickup/refusal envia direto e navega)
2. **Validação do número do pedido** (se `photo_reference`): botão "Validar número" chama `POST /proof/reference` — se correto mostra "✓ Número do pedido correto", se incorreto mostra alert "Número do pedido incorreto" em vermelho. Input fica disabled após validação. Ao alterar o valor, reseta a validação.
3. **Botão "Finalizar entrega"**: só aparece quando foto está pronta E (se `photo_reference`) referência está validada. Ao clicar, envia a foto ao backend e navega para tela de conclusão. Mostra spinner "Finalizando..." enquanto processa.
