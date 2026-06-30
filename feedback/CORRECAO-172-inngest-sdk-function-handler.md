# CORRECAO-172 — Inngest SDK: function handler e endpoint /api/inngest

## O que mudou
Adicionado o SDK oficial do Inngest (`inngest>=0.4,<1`) e criado o endpoint
`/api/inngest` que o Inngest chama para executar a função agendada.

## Por que era necessário
A implementação anterior enviava eventos via REST API (`POST /e/{event_key}`)
mas não registrava nenhuma função — o Inngest não sabia para onde chamar de volta.
O SDK resolve isso montando um handler em `/api/inngest`.

## Fluxo completo agora
1. Loja cria entrega agendada → API envia evento `delivery/scheduled-release` ao Inngest
2. No horário agendado, Inngest chama `POST /api/inngest`
3. A função `release-scheduled-delivery` executa: transita `AGENDADA → CRIADA` e chama `enqueue_dispatch()`
4. Cascade de despacho segue o fluxo normal

## Arquivos alterados
- `apps/api/pyproject.toml` — adicionado `inngest>=0.4,<1`
- `apps/api/uv.lock` — atualizado (inngest v0.5.19 + jcs v0.2.1)
- `apps/api/app/integrations/inngest_functions.py` — **NOVO**: cliente Inngest SDK + função `release-scheduled-delivery` + `register_inngest(app)`
- `apps/api/app/main.py` — chama `register_inngest(app)` no `create_app()`

## Configuração no painel do Inngest
URL do App a registrar: `https://<ngrok-url>/api/inngest`
