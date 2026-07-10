# CORRECAO-227 — Fluxo de pagamento PIX antes de despachar entregador

## Data
2026-07-09

## Mudança
Implementado fluxo completo de cobrança PIX antes do despacho de entregadores.
A loja vê o maior preço das equipes selecionadas, confirma, paga via PIX para a
subconta itcast, e só então os entregadores são chamados.

## Novo estado de entrega
- `AGUARDANDO_PAGAMENTO`: entrega criada, PIX gerado, aguardando confirmação de pagamento
  - transições: `AGUARDANDO_PAGAMENTO → CRIADA` (PIX pago) ou `→ CANCELADA`

## Fluxo completo
1. Loja seleciona equipes → frontend calcula `maxPriceCents` (maior `price_cents ?? preco_minimo_cents` dos entregadores das equipes selecionadas)
2. Botão muda de "Chamar entregador" para **"Pagar e chamar entregador"**
3. Clique abre modal de confirmação mostrando o valor máximo
4. Confirmar → cria entrega em `AGUARDANDO_PAGAMENTO` via API com `platform_pix=true` + `pix_amount_cents`
5. API gera PIX via Safe2Pay (`charge_with_split` com `jaxego_recipient` como split) → retorna `pix_qr_code` + `pix_qr_code_base64`
6. Frontend exibe tela PIX com QR code + código copia-e-cola
7. Frontend faz polling a cada 5s em `GET /v1/deliveries/{id}/pix-status`
8. Quando webhook Safe2Pay confirma pagamento → worker transiciona para `CRIADA` → chama `enqueue_dispatch`
9. Frontend detecta `paid=true` e navega para `/loja/entregas/{id}`

## Arquivos alterados

### Backend
- `alembic/versions/0043_delivery_pix_fields.py` — ADD COLUMN `pix_transaction_id`, `pix_qr_code`, `pix_qr_code_base64`
- `deliveries/models.py` — `AGUARDANDO_PAGAMENTO` em `DELIVERY_STATES`, 3 novas colunas
- `deliveries/state_machine.py` — `AGUARDANDO_PAGAMENTO: {"CRIADA", "CANCELADA"}` em `DELIVERY_TRANSITIONS`
- `deliveries/schemas.py` — `platform_pix`, `pix_amount_cents` em `CreateDeliveryBody`; `pix_qr_code`, `pix_qr_code_base64` em `CreateDeliveryResponse`
- `deliveries/service.py` — `pix_payment_port` param; bloco PIX; `AGUARDANDO_PAGAMENTO` no custo de cancelamento zero
- `deliveries/router.py` — `preco_minimo_cents` em `teams_for_address`; `pix_payment_port` no `create_delivery`; novo endpoint `GET /{id}/pix-status`
- `payments/repo.py` — nova função `get_charge_by_delivery()`
- `workers/tasks.py` — branch `charge.kind == "delivery"` em `process_safe2pay_event`: transiciona e despacha

### Frontend (web)
- `delivery.models.ts` (shared) — `platform_pix`, `pix_amount_cents` em `CreateDeliveryRequest`; `pix_qr_code`, `pix_qr_code_base64` em `CreateDeliveryResponse`
- `state-badge.component.ts` — `AGUARDANDO_PAGAMENTO` em `DeliveryState` e `META`
- `nova-entrega.page.ts` — `preco_minimo_cents` no `TeamOnline`; `maxPriceCents` computed; signals PIX; `doSubmit(platformPix)` separado do `submit()`; `startPixPolling`, `stopPixPolling`, `copyPixCode`, `cancelPixPayment`
- `nova-entrega.page.html` — exibição do preço máximo; modal de confirmação PIX; tela PIX com QR + copia-e-cola + polling indicator
- `nova-entrega.page.scss` — estilos do modal, tela PIX, preço máximo

## Breakdown do valor PIX
`pix_amount_cents = max_corrida + taxa_pix_cents + taxa_servico_cents`

Exemplo: R$ 4,00 (corrida) + R$ 0,50 (taxa PIX) + R$ 1,00 (taxa serviço) = **R$ 5,50**

- `teams_for_address` agora retorna `plan_taxa_pix_cents` e `plan_taxa_servico_cents` do plano ativo do merchant
- Frontend exibe a tabela de breakdown antes do botão e no modal de confirmação
- `totalPixCents = maxPriceCents + planTaxaPixCents + planTaxaServicoCents`
- O valor enviado como `pix_amount_cents` é o total (não só a corrida)

## Observações
- Migration copiada para container via `docker cp` + `alembic upgrade head`
- API e worker reiniciados
- Entrega agendada (`deliveryMode=scheduled`) não passa pelo fluxo PIX — mantém submit direto
- `cancellation_cost_cents` atualizado: `AGUARDANDO_PAGAMENTO` retorna 0 (sem custo de cancelar antes de pagamento)
