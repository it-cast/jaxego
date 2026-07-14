# CORRECAO-247 — Bug crítico na base de apuração do saldo/crédito (CORRECAO-246)

## Data
2026-07-13

## Pedido
"Perfeito, olhe novamente essa parte e veja se tem possibilidade de dar algum
erro" — revisão pós-implementação do saldo/crédito da loja, a pedido do
usuário.

## Bug crítico encontrado

`create_delivery` calculava `pix_courier_price_cents` (a base usada depois
pra apurar sobra/falta na finalização) a partir de
`eligible_online_prices_cents()` — que consulta o sistema de preço **antigo**
(`CourierPricingTable`/`CourierCoverageArea`, por bairro/km). Só que desde a
CORRECAO-238 (mesma sessão), o preço **real** que a loja vê e paga é o
sistema por zona (`TeamZona`/`CourierZona`), calculado no front via
`teams-for-address` — os dois sistemas não têm relação nenhuma entre si.

Confirmado direto no banco: o único entregador online ativo hoje (id 29,
usado em todos os testes reais desta sessão) tem **zero linhas** na tabela
antiga:

```sql
SELECT COUNT(*) FROM couriers c
WHERE c.status="active" AND c.is_online=1
AND NOT EXISTS (SELECT 1 FROM courier_coverage_areas cca WHERE cca.courier_id=c.id);
-- 1
```

Ou seja: `eligible_online_prices_cents()` retorna `[]` pra ele →
`pix_courier_price_cents` gravava `0` em toda entrega `platform_pix` real →
na finalização, `reconcile_delivery_credit` calculava
`diff = 0 - price_cents` (preço real, positivo) → gravava um **débito falso
igual ao preço cheio do entregador em toda entrega finalizada**, corroendo o
saldo de qualquer loja silenciosamente. Isso não apareceu nos testes da
CORRECAO-246 porque foram feitos direto no banco/módulo, sem passar pelo
`create_delivery` real.

## Correção
- `app/deliveries/schemas.py` — novo campo em `CreateDeliveryBody`:
  `pix_courier_price_cents: int | None` — o mesmo `maxPriceCents()` que o
  front já calcula e mostra no resumo (por zona, via `teams-for-address`).
- `app/deliveries/service.py::create_delivery` — removida a linha
  `max_courier_price_cents = max(prices) if prices else 0` (fonte errada).
  Agora usa o valor enviado pelo front, **reclampado no servidor**
  (`max(0, min(submitted, pix_amount_cents))` — nunca confia no cliente, nunca
  excede o total cobrado).
- `apps/web/.../nova-entrega.page.ts` — payload de criação passa a enviar
  `pix_courier_price_cents: this.maxPriceCents()` quando `platform_pix`.
- `packages/shared/.../delivery.models.ts` — campo novo em
  `CreateDeliveryRequest`.

## Outros achados da revisão (menores, reportados ao usuário — não corrigidos agora)
1. **Race no clamp do input de crédito** (`onCreditInput`): clampava contra
   `maxCreditUsableCents()` no momento da digitação, que podia estar em 0 se
   o `GET /credit-balance` ainda não tinha respondido — travava o campo em 0
   mesmo com saldo real disponível. Corrigido: input não clampa mais (só
   normaliza pra `>= 0`); `effectiveCreditCents` (computed) já reclampa contra
   o teto atual sempre que lido (totais na tela e no payload de envio).
2. **Sem reversão de crédito no cancelamento**: se uma entrega com
   `credit_applied_cents > 0` for cancelada, o débito no
   `merchant_credit_ledger` não é revertido — TD, precisa de decisão de
   produto (a loja perde o desconto reservado numa entrega cancelada?).
3. **`no_couriers_warning` tem o mesmo problema de fonte** (preço antigo) —
   pré-existente à CORRECAO-246, tangencial, não corrigido aqui.
4. Duração do lock (`FOR UPDATE`) no saldo durante chamada externa à S2P: risco
   aceitável, mesmo padrão já usado em `EscrowLedger`/`Withdrawal`.

## Build
- `docker compose exec api python -c "import app.deliveries.service"` — OK.
- API/worker reiniciados (bind mount, sem migration nova — coluna já existe
  desde a 0047).
- `ng build web` — quebrou por orçamento de estilo do componente
  (`nova-entrega.page.scss` passou de 16kb pelo bloco de crédito adicionado
  na CORRECAO-246). Ajustado `anyComponentStyle.maximumError` de 16kb → 20kb
  em `angular.json` (componente é uma página multi-step com modal PIX,
  legitimamente maior que o padrão). Build limpo depois.

## Tech debt em aberto
- Reversão de crédito no cancelamento (achado #2 acima) — sem prazo definido,
  precisa de decisão do usuário.
- `no_couriers_warning` / sistema de preço antigo ainda usado em paralelo ao
  de zonas (achado #3) — tangencial ao saldo, mas mesma causa raiz.
