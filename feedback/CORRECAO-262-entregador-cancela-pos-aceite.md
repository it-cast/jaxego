# CORRECAO-262 — Entregador cancela entre o aceite e a coleta, reabre a fila

## Data
2026-07-14

## Pedido
"Tem que ser possível o entregador cancelar a entrega, depois de aceita e
antes de ser coletada. Se ele fizer isso, precisa reabrir a entrega e montar
novamente a fila."

## Desenho
Isso é diferente do cancelamento da LOJA (CORRECAO-249/250, que hoje só é
permitido pré-aceite e termina em `CANCELADA`). Aqui é o ENTREGADOR desistindo
depois de já ter aceitado — a entrega não deve morrer, tem que voltar pra
fila pros outros entregadores poderem pegar. Reusei a infraestrutura de
despacho que já existe (a mesma que atende uma entrega nova ou uma recusa
ativa pré-aceite), não criei um mecanismo de fila novo:

1. **State machine** (`state_machine.py`): nova transição `ACEITA → CRIADA`
   (só essa — `COLETADA` continua sem volta, exatamente o limite que você
   pediu: "depois de aceita e antes de ser coletada").
2. **Serviço** (`deliveries/service.py::courier_cancel_acceptance`): carrega
   a entrega checando que é do entregador (`get_courier_delivery`, 404 se
   não for — mesma proteção IDOR de sempre), rejeita com 422 se não estiver
   em `ACEITA` (`DeliveryNotAcceptedError`), transiciona pra `CRIADA` e
   limpa `courier_id`/`price_cents`/`accepted_at` (o próximo que aceitar
   seta os dele de novo, igual em qualquer aceite normal).
3. **Endpoint** (`couriers/router.py::cancel_acceptance`, `POST
   /v1/couriers/{courier_id}/deliveries/{delivery_id}/cancel-acceptance`):
   depois do commit, dispara os efeitos de fila (fora da transação do banco,
   mesmo padrão de `enqueue_payout`/`enqueue_refund`):
   - `offer_state.add_declined` — marca esse entregador como "já recusou"
     pra essa entrega, pra ele não ser oferecido de novo na mesma rodada
     (mesmo tratamento que uma recusa ativa antes do aceite já tem).
   - `enqueue_dispatch` — a MESMA função usada quando uma entrega nova é
     criada. Ela reconstrói a fila de candidatos (excluindo o entregador que
     acabou de desistir) e abre a primeira oferta.
4. **Log de auditoria** (`tracking/service.py`): nova ação
   `cancelou_aceite`, mesma tabela `delivery_locations` já criada no
   CORRECAO-252 — GPS obrigatório, mesmo padrão das outras ações do
   entregador.

## Frontend (app do entregador)
`entrega-ativa.page.ts` — na tela da entrega, enquanto o estado é `ACEITA`,
apareceu um botão secundário "Cancelar entrega" ao lado de "Já coletei".
Confirmação antes (`jx-confirm-dialog`, mesmo padrão do CORRECAO-245),
avisando explicitamente que a entrega volta pra fila pra outro entregador.
GPS obrigatório (mesmo padrão de coletar/chegar/entregar). Depois de
cancelar com sucesso, sai da tela (a entrega deixou de ser dele) e volta pro
`/entregador/inicio`.

## Validado
Testado direto contra o banco com uma entrega real de teste:
- Criada → forçado ACEITA (courier_id=15, price_cents=500) →
  `courier_cancel_acceptance` → confirmado: `state=CRIADA`,
  `courier_id=None`, `price_cents=None`, `accepted_at=None`.
- Testado o limite: entrega em `COLETADA` → tentativa de cancelar → 422
  `"Só é possível cancelar entre o aceite e a coleta."` (exatamente o
  escopo pedido).
- Ownership: `get_courier_delivery` já filtra por courier_id — um
  entregador não pode cancelar aceite de entrega de outro (404, não 403,
  mesmo padrão anti-enumeração de sempre).
- Endpoint confirmado registrado (`POST .../cancel-acceptance`).
- `ng build app` — verde. API reiniciada.
- Dado de teste levado a um estado terminal real (`FINALIZADA`, via
  transições legítimas) no final, sem deixar entrega fantasma ativa pro
  entregador de teste.

## Não testado
Não testei o disparo real do `enqueue_dispatch`/`add_declined` (precisaria
de Redis + arq worker rodando o cascade de verdade, com um segundo
entregador elegível pra confirmar que a oferta chega pra ele e não pro que
cancelou). A lógica reusa funções já testadas neste mesmo projeto
(`enqueue_dispatch` é literalmente a mesma chamada usada em toda criação de
entrega; `add_declined` é a mesma de uma recusa ativa) — risco baixo, mas
fica registrado que não foi um teste ponta-a-ponta com dois entregadores
reais.

## Bug encontrado no teste real do usuário (mesmo dia)
Testou de verdade (courier 29, entrega 125) e deu 500:
`AttributeError: 'int' object has no attribute 'area_id'`. Causa: usei
`scope.area_id` no endpoint, mas em `couriers/router.py` o `AreaScopeDep` é
`int | None` (o próprio area_id), não um objeto — diferente do
`MerchantScopeDep` usado em `deliveries/router.py`, que É um dataclass com
`.area_id`. Confundi os dois padrões. Corrigido removendo o parâmetro
`area_id` de `courier_cancel_acceptance()` inteiramente — ele nem era usado
dentro da função (a checagem de dono já é só por `courier_id` via
`get_courier_delivery`). Entrega 125 não foi afetada (erro aconteceu antes
de qualquer escrita — `transition()` faz o `SELECT ... FOR UPDATE` dentro da
mesma chamada que já tinha quebrado antes de chegar lá). API reiniciada.

## Tech debt / pontos em aberto
- Se `enqueue_dispatch` falhar silenciosamente (fila fora do ar), a entrega
  fica `CRIADA` sem oferta ativa até o cron `redispatch_stale_deliveries`
  (a cada 5 min) resgatar — mesmo comportamento best-effort já aceito em
  outros pontos do sistema, não é uma falha nova introduzida aqui.
