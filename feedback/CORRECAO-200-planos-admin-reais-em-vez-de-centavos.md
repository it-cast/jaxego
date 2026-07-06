---
classe: ux
data: 2026-07-06
arquivos_afetados:
  - apps/web/src/features/admin-plataforma/planos.page.ts
  - apps/web/src/features/admin-plataforma/planos.page.html
---

## Problema
O formulário de criação/edição de planos em `/plataforma/planos` exibia os campos de preço e taxa em centavos, obrigando o admin a digitar `9990` para representar R$ 99,90.

## Implementação
- `showEdit()`: valores `price_cents` e `fee_cents` do plano divididos por 100 ao preencher o formulário
- `save()`: valores do formulário multiplicados por `Math.round(x * 100)` antes de enviar para a API (`Math.round` evita erros de ponto flutuante como `99.9 * 100 = 9989.999...`)
- HTML: labels "Preco (centavos)" → "Preco (R$)" e "Taxa por entrega (centavos)" → "Taxa por entrega (R$)"
- Inputs: adicionado `step="0.01"` e `placeholder="0,00"` para aceitar decimais
- Tabela de listagem não foi alterada — já exibia em reais via `formatCents()`
