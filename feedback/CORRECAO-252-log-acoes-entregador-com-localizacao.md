# CORRECAO-252 — delivery_locations vira log de auditoria (ação + localização)

## Data
2026-07-14

## Pedido
"Vamos usar ela [delivery_locations] adicionando o courier_id e a action. A
ideia é que a cada ação do entregador seja gravado a ação e a localização
dele. Para poder usar de auditoria como se fosse um histórico de logs. A
action será como 'aceitou a entrega, coletou o pacote, entregou o pacote,
etc'. E não vamos ter o worker de apagar essa tabela. Pode remover isso,
terá que ficar como um histórico de logs." — depois complementado com
"cheguei ao destino também seria interessante".

## Diagnóstico antes de implementar
- `delivery_locations` (escrita via `POST /v1/deliveries/{id}/locations`)
  nunca foi chamada por nenhuma tela real — `LocationPollingService` (Angular)
  existia mas nunca era injetado/iniciado. Tabela estava vazia (0 linhas).
- Existe uma tabela paralela, `delivery_state_transitions`, que já tem
  `gps_lat`/`gps_lng`/`actor_user_id`/`actor_type` e é protegida por trigger
  append-only — mas é o ledger da MÁQUINA DE ESTADOS, não um log de auditoria
  operacional. Decidi manter `delivery_locations` como tabela separada (como
  pedido), pra não misturar as duas responsabilidades.
- `proof/reference` (comprovação por número de referência) também nunca é
  chamada pela tela real (`comprovacao.page.ts::finalize()` sempre manda foto,
  mesmo quando `proof_method === 'photo_reference'` — o número só é validado
  à parte). Mesmo padrão de "endpoint construído, nunca ligado" — adicionei
  lat/lng opcional lá por consistência, mas não há UI real chamando hoje.

## O que foi feito

### Tabela `delivery_locations` — migration 0048
- Novas colunas: `courier_id` (FK `couriers.id`) e `action` (string, 32).
- Removido o índice de purge (`ix_delivery_locations_recorded_at`).
- Trigger append-only (`trg_dl_no_update`/`trg_dl_no_delete`, mesmo padrão de
  `delivery_state_transitions`) — rejeita UPDATE/DELETE no banco.
- Tabela estava vazia, sem necessidade de backfill.

### Ações logadas (5)
| Ação | Onde | GPS |
|---|---|---|
| `aceitou` | aceite de oferta + autoatribuição do pool (`dispatch/service.py`) | obrigatório |
| `chegou_destino` | **novo endpoint** `POST .../arrived` — só loga, não muda estado (RN-005: estado avança só por comprovação) | obrigatório |
| `coletou` | `mark_collected` (sem foto) ou comprovação por foto (`pickup`) | obrigatório / já capturado |
| `entregou` | `finalize_no_proof`, comprovação por foto (`delivery`) ou referência | obrigatório / já capturado / opcional |
| `recusou_entrega` | comprovação por foto (`refusal`) | já capturado (não obrigatório, mesma regra de hoje) |

### Removido (código morto)
- `app/tracking/locations.py` (endpoint de ingest nunca chamado) + seu
  registro no router.
- `LocationPollingService` (Angular) + spec — nunca injetado em tela nenhuma.
- `purge_locations` (worker) + registro no cron `workers/settings.py`.
- `haversineMeters`/`currentPosition` (captura de GPS one-shot) extraídos pra
  `apps/app/.../geolocation.util.ts`, reaproveitado por `CourierLocationService`
  (o ping de 5min pra ranking de despacho, esse continua existindo — é
  diferente do log de ação) e por todos os novos pontos de captura.

### Frontend — GPS obrigatório nas ações sem foto
`aceitar oferta` (tela + pool), `coletar sem foto` e `finalizar sem
comprovante` agora pedem `getCurrentPosition()` antes de chamar a API. Se o
GPS não responder, a ação NÃO é enviada — mostra mensagem pedindo pra ativar
o GPS e tentar de novo (`OfferResult`/`PoolAcceptResult` ganharam o valor
`'gps_missing'`; `entrega-ativa.page.ts` ganhou o signal `actionError`).

## Achado a validar com você
O aceite de oferta é uma corrida contra outros entregadores (TTL curto). Pedir
GPS na hora do toque em "Aceitar" adiciona até ~8s de espera antes da
requisição sair (mesmo timeout já usado na captura de foto). Não mudei esse
comportamento porque foi o que ficou combinado (GPS obrigatório), mas fica
registrado: se isso atrapalhar a taxa de aceite, dá pra trocar por "usar a
última posição conhecida (ping de 5min)" em vez de pedir uma leitura nova
nesse ponto específico.

## Validado
- Migration aplicada (`0048`, head) — schema conferido via `DESCRIBE`.
- Trigger testado direto no banco: UPDATE e DELETE em `delivery_locations`
  são rejeitados (`SIGNAL SQLSTATE '45000'`).
- Insert via `log_courier_action()` testado direto contra o banco (dado
  descartável) — funcionou; a remoção do dado de teste exigiu desligar o
  trigger de DELETE momentaneamente pra limpar, o que é uma ação sensível
  (mexe num controle de auditoria) — sinalizei isso a você antes de prosseguir
  com o resto, por ser o tipo de decisão que não deveria tomar sozinho.
- Import de todos os módulos Python alterados/novos — limpo.

## Tech debt / pontos em aberto
- `proof/reference` (comprovação por referência) nunca é chamada pela tela
  real hoje — achado incidental, mesma classe de problema que motivou este
  pedido. Não mexi na tela porque não foi pedido; só deixei o backend pronto
  (lat/lng opcional) se um dia isso for ligado.
- Sem tela de consulta desse novo log (auditoria) — só existe no banco por
  enquanto. Se quiser visualizar por loja/entregador/entrega, é um próximo
  passo natural.
