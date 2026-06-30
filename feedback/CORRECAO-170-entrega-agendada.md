# CORRECAO-170 — Entrega agendada via Inngest

## Funcionalidade
A loja pode agendar uma entrega para um horário futuro. Em vez de despachar o
entregador imediatamente, a entrega nasce no estado `AGENDADA` e o Inngest é
chamado para disparar o despacho no horário exato.

## Fluxo
1. Loja cria entrega com `scheduled_at` (ISO-8601 UTC, mínimo 5 minutos no futuro)
2. API persiste em estado `AGENDADA`, registra `scheduled_at`, envia evento ao Inngest
3. Inngest guarda o `inngest_event_id` retornado (para rastreabilidade)
4. No horário agendado, Inngest chama `POST /v1/deliveries/scheduled/release`
5. Endpoint verifica assinatura HMAC-SHA256 (`x-inngest-signature`), transita
   `AGENDADA → CRIADA` e chama `enqueue_dispatch(delivery_id)`
6. Cascade de despacho segue o fluxo normal

## Cancelamento
Se a loja cancela antes do horário: transita `AGENDADA → CANCELADA` com custo zero
(RN-004). O Inngest ainda chamará o webhook, mas a função detecta que o estado não é
`AGENDADA` e retorna 200 sem efeito (idempotente).

## Arquivos alterados

### Backend
- `apps/api/alembic/versions/0030_scheduled_delivery.py` — migration: ADD COLUMN scheduled_at DATETIME NULL, inngest_event_id VARCHAR(128) NULL
- `apps/api/app/deliveries/models.py` — adicionado `AGENDADA` a `DELIVERY_STATES`; campos `scheduled_at` e `inngest_event_id` ao modelo `Delivery`
- `apps/api/app/deliveries/state_machine.py` — adicionado `AGENDADA` com transições `→ CRIADA` e `→ CANCELADA`
- `apps/api/app/deliveries/schemas.py` — `scheduled_at: datetime | None` em `CreateDeliveryBody` (com validator de mínimo 5 min); `scheduled_at: str | None` em `DeliveryOut` e `CreateDeliveryResponse`
- `apps/api/app/deliveries/service.py` — `create_delivery` detecta `scheduled_at` → estado inicial `AGENDADA` + chama Inngest; `cancellation_cost_cents` trata `AGENDADA` como custo zero; nova função `release_scheduled_delivery`
- `apps/api/app/deliveries/router.py` — `create_delivery` não chama `enqueue_dispatch` para `AGENDADA`; `_delivery_out` expõe `scheduled_at`; novo endpoint `POST /scheduled/release` com verificação de assinatura Inngest
- `apps/api/app/integrations/inngest.py` — **NOVO**: `InngestClient` (real, httpx) + `InngestClientStub` (dev/test) + `get_inngest_client()`
- `apps/api/app/core/config.py` — settings: `inngest_event_key`, `inngest_signing_key`, `inngest_api_url`

### Shared / Frontend
- `packages/shared/src/shared/models/delivery.models.ts` — `scheduled_at?: string | null` em `CreateDeliveryRequest` e `CreateDeliveryResponse`

## Banco de dados
Migration `0030_scheduled_delivery` aplicada com sucesso.

## Configuração necessária (produção)
```env
INNGEST_EVENT_KEY=<event-key-do-inngest>
INNGEST_SIGNING_KEY=<signing-key-do-inngest>
```
Em dev/test sem essas variáveis, o stub é usado automaticamente (sem rede).
