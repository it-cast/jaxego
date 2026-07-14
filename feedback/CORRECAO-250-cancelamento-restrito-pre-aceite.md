# CORRECAO-250 — Cancelamento restrito a pré-aceite

## Data
2026-07-13

## Pedido
Depois de investigar a CORRECAO-249 (estorno preso em cancelamento
pós-aceite), perguntei se fazia sentido só permitir cancelar antes do
entregador aceitar, já que o custo RN-004 (50%/100%) nunca virou cobrança
real. Usuário confirmou: "faça isso, deixe a possibilidade do cancelamento
antes do entregador aceitar".

## Mudança
Cancelamento agora só é possível em `AGENDADA`, `AGUARDANDO_PAGAMENTO`,
`CRIADA`, `SEM_RESPOSTA` — todos estados onde nenhum entregador aceitou
ainda. `ACEITA` e `COLETADA` não têm mais `CANCELADA` como transição válida.

## Arquivos

### Backend
- `app/deliveries/state_machine.py` — removido `CANCELADA` de
  `DELIVERY_TRANSITIONS["ACEITA"]` e `["COLETADA"]`. Essa é a trava de
  verdade (enforced no `transition()`, 422 se tentado via API direto — não
  só esconder botão no front).
- `app/deliveries/service.py::cancellation_cost_cents` — simplificada pra
  sempre retornar 0 (as branches ACEITA 50%/COLETADA 100%+retorno ficaram
  inalcançáveis, já que o state machine barra antes). `return_pct` mantido
  na assinatura pra quando a Phase 11 (faturamento) reintroduzir um custo
  pós-aceite de verdade.
- `tests/deliveries/test_cancel_cost.py` — reescrito: todas as 10 estados
  testados retornam custo 0; removidos os testes de 50%/100% (cenário não
  existe mais). Também corrigido `estimate_max_cents` → `price_cents` no
  helper de teste (campo que não existe mais no model — bug pré-existente
  no teste antigo, não relacionado a esta mudança).

### Frontend
- `apps/web/.../entrega-detalhe/entrega-detalhe.page.ts` — `canCancel()` não
  inclui mais `ACEITA`/`COLETADA`; `cancelLabel()` simplificado (sempre
  "Cancelar (sem custo)", já que só sobram estados grátis).
- `apps/web/.../entregas/entregas-list.page.ts` + `delivery-row.component.ts`
  — já só expunham cancelar em `CRIADA`; nada a mudar.

## Não rodei a suíte de testes
`docker compose exec api pytest` — imagem de produção não tem pytest
instalado. `uv run pytest` local falhou na COLETA (não no que eu mudei):
`tests/conftest.py` ainda importa `User` de `app.auth.models`, removido
num refactor anterior desta sessão (antes da CORRECAO-235) — suíte inteira
já estava quebrada nesse ponto, pré-existente, fora de escopo aqui.
Validei a mudança direto no runtime do container (script inline): confirmei
que `ACEITA→CANCELADA` e `COLETADA→CANCELADA` agora levantam
`InvalidTransitionError`, que `CRIADA→CANCELADA` continua permitido, e que
`cancellation_cost_cents` retorna 0 pra `ACEITA`.

## Build
- Import limpo (`docker compose exec api python -c "import ..."`).
- API + worker reiniciados.
- `ng build web` — verde.

## Tech debt em aberto
- Suíte de testes do backend não coleta (`tests/conftest.py` importa `User`
  removido) — pré-existente, precisa de correção separada se algum dia
  quiser rodar a suíte completa de novo.
- Se a Phase 11 (faturamento) um dia quiser reabrir cancelamento
  pós-aceite com custo real, `cancellation_cost_cents`/`cancel_cost_cents`
  seguem no lugar como esqueleto — só precisa reintroduzir os alvos no
  `DELIVERY_TRANSITIONS` e a lógica de cobrança/repasse de verdade.
