---
classe: fix+feature
data: 2026-07-07
arquivos_afetados:
  - apps/api/app/payments/safe2pay_adapter.py
  - apps/api/app/payments/subscriptions.py
  - apps/api/app/payments/router.py
  - apps/api/app/payments/port.py
  - apps/api/app/payments/safe2pay_stub.py
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.html
  - apps/web/src/features/loja/cadastro/cadastro.page.scss
  - apps/web/src/features/loja/cadastro/merchant.service.ts
---

## Problemas corrigidos

### 1. Acentos rejeitados pelo Safe2Pay em campos de endereço
Safe2Pay retornava 422: `"CityName é inválido"` para "Santo Antônio de Pádua".
**Fix:** helper `_ascii()` com `unicodedata.normalize("NFD")` aplicado em `Street`, `District`, `CityName`.

### 2. Telefone com +55 rejeitado pelo Safe2Pay
Safe2Pay exige 10–11 dígitos com DDD, sem código de país.
Estávamos enviando `+5522988076272` (13 dígitos).
**Fix:** helper `_s2p_phone()` que strip o `+55` antes de enviar.

### 3. Resposta Safe2Pay em camelCase, não PascalCase
A spec documenta `QrData`, `ImmediatePayment`, mas a API retorna `qrData`, `immediatePayment`.
`qr_code` e `qr_code_base64` ficavam `None` — QR Code nunca exibia.
**Fix:** parsing com fallback: `data.get("qrData") or data.get("QrData")` etc.

### 4. `qr_code_base64` hardcoded como `None`
`QrData.qrCode` é URL de imagem (não base64). Estava sendo ignorado.
**Fix:** `qr_code_base64=qr_data.get("qrCode")` e frontend usa `[src]="pixQrB64()"` diretamente (sem prefixo `data:image/png;base64,`).

### 5. `billing_status` ficava `trial` após criar PIX
`activate_pix` nunca setava `billing_status = "pending"`.
**Fix:** adicionado `sub.billing_status = "pending"` em `subscriptions.py`.

### 6. Webhook inexistente — polling sem atualização
Sem webhook configurado, ninguém atualizava o status após aprovação do PIX.
**Fix:** `GET /assinatura` consulta Safe2Pay diretamente via `GET /v3/pix/automatic/authorizations/{id}`
quando `billing_status = "pending"`. Se Safe2Pay retornar `APROVADA`/`ATIVA`, atualiza o banco na hora.
Novo método: `get_pix_authorization_status` em `port.py`, `safe2pay_adapter.py` e `safe2pay_stub.py`.

### 7. Histórico de cobranças mostrava registros de outras lojas
Query `GET /cobrancas` filtrava por `area_id` — exibia cobranças de todas as lojas da área.
**Fix:** join com `merchant_subscriptions` filtrando por `merchant_id`.

### 8. Polling no frontend sem destino
Frontend ficava mostrando QR indefinidamente sem detectar pagamento.
**Fix:** polling a cada 5s em `GET /v1/payments/assinatura`. Quando `billing_status = "active"`,
para o timer e redireciona para `/loja/cadastro/sucesso`. `ngOnDestroy` limpa o timer.

## Features adicionadas

### Toggle CPF/CNPJ removido — auto-detecção por dígitos
Removido select "Tenho CNPJ / Sou autônomo (CPF)".
Campo inicia com máscara CPF. Ao digitar o 12º dígito, troca automaticamente para CNPJ.
`maxlength="18"` (CNPJ max) para não bloquear o browser antes do handler disparar.
Label fixo: `CPF/CNPJ`.

### QR Code — ajustes de UX
- Removido `height: 200px` do `.jx-cadastro__pix-qr` (imagem ficava "amassada")
- Adicionado botão "Copiar código PIX" abaixo do campo copia-e-cola
- Removido botão "Ir para a loja" (usuário precisa pagar antes de sair)

## Lições aprendidas

- **Safe2Pay v3 usa camelCase nas respostas**, diferente da spec (PascalCase). Sempre logar a resposta raw antes de parsear.
- **Safe2Pay rejeita acentos** em campos de endereço. Normalizar com `unicodedata` antes de enviar.
- **Safe2Pay exige telefone sem +55**, apenas DDD + número (10–11 dígitos).
- **PIX Automático não tem CallbackUrl por request** — webhook é configurado no dashboard OU polling da API é necessário.
- **`maxlength` no browser bloqueia o handler Angular** — para auto-switch de máscara, deixar `maxlength` no máximo sempre.
- **Query de cobrança por `area_id` é incorreta** — usar join com `merchant_subscriptions` por `merchant_id`.
- **Ao deletar loja em testes**, incluir `platform_charges` na limpeza (via subscription_id).
