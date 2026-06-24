# Correção 099 — Avaliação do entregador pela loja no detalhe da entrega

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/features/loja/entregas/delivery.service.ts` — método `rate(deliveryId, stars, comment)`
- `apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.ts` — seção de avaliação com estrelas + comentário
- `apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.scss` — estilos da avaliação

## Implementação

- Quando a entrega está `FINALIZADA`, exibe seção "Avaliar entregador" na lateral do detalhe
- 5 estrelas clicáveis (★) com destaque em brand color
- Textarea para comentário opcional (max 500 chars)
- Botão "Enviar avaliação" chama `POST /v1/deliveries/{id}/rating`
- Após enviar, exibe "Avaliação enviada. Obrigado!" e esconde o formulário
- Se já foi avaliada (409), o service retorna false silenciosamente
