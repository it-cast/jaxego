---
classe: feature
data: 2026-07-06
arquivos_afetados:
  - apps/api/app/payments/port.py
  - apps/api/app/payments/safe2pay_adapter.py
  - apps/api/app/payments/safe2pay_stub.py
  - apps/api/app/payments/schemas.py
  - apps/api/app/payments/subscriptions.py
  - apps/api/app/payments/router.py
  - apps/api/app/workers/tasks.py
  - apps/api/app/workers/settings.py
  - apps/web/src/features/loja/cadastro/merchant.models.ts
  - apps/web/src/features/loja/plano/billing.service.ts
  - apps/web/src/features/loja/plano/plano.page.ts
  - apps/web/src/features/loja/plano/plano.page.scss
---

## Problema

PIX não tinha suporte a recorrência. O método `create_pix_authorization` usava `/v2/payment` (PaymentMethod 10) que gera apenas um QR Code avulso — sem recorrência real. Não havia cron para cobranças PIX futuras nem ativação da assinatura quando o QR era pago.

## Implementação

### Backend — duas modalidades de PIX

**PIX avulso (pix_recorrente=false):**
- Manteve `/v2/payment` PaymentMethod 10 (QR Code único)
- `process_safe2pay_event` agora chama `activate_pix_on_charge_paid()` quando a cobrança PIX de assinatura é confirmada paga → ativa `billing_status = "active"` e define `due_at`

**PIX Automático BACEN (pix_recorrente=true):**
- Novo endpoint `/v3/pix/automatic/authorizations` via helper `_post_v3()` (sem HasError wrapper — REST v3 usa HTTP status codes)
- Payload `[ASSUMIDO DEC-PIX-01]`: `Contract.Calendar.ExpirationSeconds`, `RetryPolice: PERMITE_3R_7D`, `Customer` inline no contrato
- `activate_approved_pix()` — ativa assinatura quando webhook APROVADA chega
- `charge_due_pix_subscriptions()` — cron que cria `chargeSchedules` para assinaturas PIX Automático aprovadas com `due_at` vencido
- Novo endpoint `POST /v3/.../chargeSchedules` via `create_pix_charge_schedule()` `[ASSUMIDO DEC-PIX-02]`

### Correções estruturais no fluxo PIX existente

- `activate_pix()` agora seta `sub.plan_id` imediatamente (antes nunca era definido no PIX)
- `process_safe2pay_event` distingue: APROVADA de autorização PIX vs cobrança paga normal
- `SubscriptionOut` expõe `pix_autorizacao_status` para o frontend saber se aguarda aprovação

### Worker / cron

- Novo `charge_pix_subscriptions_daily` registrado como function e cron (06:05 UTC)

### Frontend

- Toggle "Ativar débito automático (PIX Recorrente)" no modal de pagamento PIX
- Botão "Gerar PIX" (avulso) ou "Autorizar PIX Recorrente" (automático)
- Após autorização PIX Automático: exibe QR/link + mensagem "Abra seu app bancário e aprove a autorização de débito automático"
- Signal `isPixAutoPending` detecta estado CRIADA para mostrar a instrução correta

## Observação

Os sub-campos de `Contract.Calendar` e `Customer` no payload v3 são `[ASSUMIDO]` — a Safe2Pay não disponibiliza sandbox para PIX Automático. Validar nomes de campo exatos no primeiro deploy em produção.
