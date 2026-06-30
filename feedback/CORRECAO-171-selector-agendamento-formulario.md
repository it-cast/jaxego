# CORRECAO-171 — Selector imediata/agendada no formulário de nova entrega

## Página afetada
- `http://localhost:4200/loja/entregas/nova`

## O que mudou
Adicionada seção "Quando" ao formulário com dois radio cards:
- **Imediata** — comportamento anterior (chama entregador agora)
- **Agendada** — exibe input `datetime-local` para escolher data e hora

Quando "Agendada" é selecionado:
- Input de data/hora aparece com `min` = agora + 5 minutos
- Validação client-side antes do submit (5 min no futuro)
- `scheduled_at` é convertido para ISO-8601 UTC e enviado no request
- Botão muda para "Agendar entrega"
- Erros de validação são exibidos inline

## Arquivos alterados
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts` — signals `deliveryMode`, `scheduledAt`, `scheduledAtError`; método `setDeliveryMode()`; getter `scheduledAtMin`; validação em `canSubmit()` e `submit()`; `scheduled_at` no request body
- `apps/web/src/features/loja/entregas/nova-entrega.page.html` — fieldset "Quando" com radio cards + input datetime-local condicional + mensagem de erro
- `apps/web/src/features/loja/entregas/nova-entrega.page.scss` — `.jx-nova__radios--2col`, `.jx-nova__datetime`, `.jx-nova__sched-err`
