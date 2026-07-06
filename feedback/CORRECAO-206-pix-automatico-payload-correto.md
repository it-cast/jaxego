---
classe: feature+fix
data: 2026-07-06
arquivos_afetados:
  - apps/api/alembic/versions/0037_merchant_address_zip_city_state.py
  - apps/api/app/merchants/models.py
  - apps/api/app/merchants/schemas.py
  - apps/api/app/merchants/service.py
  - apps/api/app/payments/port.py
  - apps/api/app/payments/router.py
  - apps/api/app/payments/subscriptions.py
  - apps/api/app/payments/safe2pay_adapter.py
  - apps/web/src/features/loja/cadastro/merchant.models.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
---

## Problema

O payload de `_create_pix_automatic` estava completamente errado em relação à documentação
oficial Safe2Pay (OpenAPI spec):

- `Calendar` dentro de `Contract` (deveria ser top-level)
- `RetryPolice` (typo) dentro de `Contract.Calendar` (campo inexistente)
- Campos obrigatórios ausentes: `Contract.Description`, `Contract.Name`,
  `Customer.Phone`, `Customer.Address` (todos os subcampos)
- `Calendar.StartDate`, `Calendar.Periodicity` ausentes (obrigatórios)
- Parsing da resposta errado: `data.get("Id")` mas v3 retorna `{"data": {"Id": ...}}`
- `PixCopyPaste` errado — campo correto é `QrData.PixCopyAndPaste`

Cron de agendamento PIX disparava quando `due_at <= agora`, mas a API exige
chargeSchedule criado **entre 2 e 10 dias antes** do vencimento.

Merchant não armazenava CEP, cidade e estado — obrigatórios pelo Safe2Pay.

## Correções

### DB / Model / Schema / Service
- Novas colunas: `address_zip` (VARCHAR 10), `address_city` (VARCHAR 120), `address_state` (VARCHAR 2)
- Migration 0037 criada e aplicada diretamente (container não monta /alembic/)
- `MerchantSignupBody` recebe os 3 novos campos (opcionais)
- `service.py` persiste os novos campos no `Merchant`

### `port.py` — Customer dataclass
- Adicionados campos opcionais: `phone`, `zip_code`, `street`, `street_number`,
  `neighborhood`, `city`, `state`

### `payments/router.py`
- No fluxo PIX, passa todos os campos de endereço e telefone do merchant para `activate_pix`

### `payments/subscriptions.py`
- `activate_pix` recebe os novos parâmetros de endereço/telefone e monta Customer completo
- Cron: corrigido para disparar quando `due_at <= agora + 3 dias`
  (Safe2Pay exige agendamento entre 2–10 dias antes do vencimento)

### `safe2pay_adapter.py` — `_create_pix_automatic` reescrito
Payload correto per OpenAPI spec:
```
Application / Contract.Description / Contract.Name / Contract.Customer (com Phone e Address completo)
Calendar top-level: StartDate, Periodicity=MENSAL, RetryPolicy=PERMITE_3R_7D
Amount.Fixed
ImmediatePayment: Amount + Reference (primeira cobrança na aprovação)
```
Parsing correto: `raw["data"]["Id"]`, `raw["data"]["QrData"]["PixCopyAndPaste"]`

### Frontend — `cadastro.page.ts`
- Form: adicionados controls `cidade` e `uf` (hidden, auto-preenchidos)
- ViaCEP: captura `localidade` → `cidade`, `uf` → `uf`
- Mapbox GPS: captura `place` → `cidade`, `region.short_code` → `uf`
- Submit: envia `address_zip` (só dígitos), `address_city`, `address_state`

### Frontend — `merchant.models.ts`
- `SignupRequest` inclui `address_zip?`, `address_city?`, `address_state?`
