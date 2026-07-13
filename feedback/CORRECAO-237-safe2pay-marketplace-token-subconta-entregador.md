# CORRECAO-237 — Criação de subconta S2P do entregador usa token da conta matriz

## Data
2026-07-13

## Diagnóstico
Ao aprovar o último documento pendente em `/equipe/entregadores/{id}`, o backend
já disparava a criação da subconta corretamente (fluxo confirmado desde a
CORRECAO-234: aprovar → todos docs aprovados → courier vira `active` →
`POST /v2/marketplace/add`). O problema era **externo ao código**: a Safe2Pay
recusava a chamada com

```
error_code: 300
"Recurso não permitido para conta diferente de Marketplace."
```

A conta associada ao `SAFE2PAY_TOKEN` (a subconta filha ITCAST, usada hoje para
todas as cobranças) não tem permissão de Marketplace habilitada — só a conta
matriz/raiz pode criar outras subcontas via esse endpoint.

## Pergunta do usuário respondida
> É necessário também a secret key da conta matriz?

Não. `SAFE2PAY_SECRET_KEY` só é usado para **validar webhooks recebidos**
(compara com o campo `SecretKey` que a Safe2Pay envia no corpo). Chamadas de
**saída** (inclusive `/v2/marketplace/add`) autenticam só via header
`x-api-key` = o token. Criar subconta não gera webhook, então só o token da
matriz é necessário.

## Mudança
Usuário adicionou `SAFE2PAY_MARKETPLACE_TOKEN` no `.env` (token da conta
matriz). Conectado no código:

- `app/core/config.py`: novo setting `safe2pay_marketplace_token`.
- `app/payments/safe2pay_adapter.py`:
  - `Safe2PayHttpAdapter.__init__` ganha `marketplace_api_key` (fallback pro
    token normal se não configurado — nunca quebra em ambientes sem o token novo).
  - Novo `_marketplace_headers()` — mesmo x-api-key, mas com o token da matriz.
  - `_call_safe2pay` ganha parâmetro opcional `headers` (override).
  - `register_subaccount_full` passa `headers=self._marketplace_headers()` —
    é a ÚNICA chamada que usa o token da matriz; todo o resto (cobrança PIX,
    cartão, split, extrato) continua na conta filha ITCAST via `SAFE2PAY_TOKEN`.
- `app/payments/factory.py`: repassa `settings.safe2pay_marketplace_token` pro
  adapter.

## Deploy
`docker-compose.yml` usa `env_file: ../.env` — variável nova exige recriar o
container (`docker compose up -d --force-recreate api worker`), `restart`
sozinho não relê o `.env`.

## Validado
Chamado `register_subaccount_full` direto (fora do fluxo HTTP, via script no
container) duas vezes:
1. Courier antigo sem `birth_date` → erro mudou de **300 → 1346** (campo
   obrigatório faltando) — confirma que a permissão de Marketplace passou.
2. Courier novo completo, mas com CPF de teste fictício (checksum válido, não é
   pessoa real) → erro **1343** (verificação Receita Federal falhou) — confirma
   que o payload é aceito integralmente; só falta CPF real pra criar de verdade.

Ambos os testes limpos do banco ao final.

## Pendência
Falta validar com um CPF real (do próprio Roger ou de um entregador de fato)
para confirmar a criação ponta a ponta com `s2p_recipient_id` preenchido.
