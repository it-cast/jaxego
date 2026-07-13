# CORRECAO-239 — Criação de subconta S2P: Tax mínima do MerchantSplit

## Data
2026-07-13

## Sintoma
Depois da CORRECAO-237 (token da matriz), a criação de subconta continuava
falhando ao aprovar os 3 documentos.

## Causa
Terceiro erro em sequência da Safe2Pay (progressão: 300 permissão → 1346 data
de nascimento → **1273 Tax**):
```
error_code: 1273
"O valor Tax informado para o PaymentMethodCode - 6 deve ser igual ou
superior a 0,35"
```
O payload de `/v2/marketplace/add` mandava `Taxes: [{"TaxTypeName": "2",
"Tax": "0"}]` — a Safe2Pay exige um valor mínimo de R$ 0,35 nesse campo pro
método PIX (código 6).

**Importante:** esse `Tax` é uma configuração da própria Safe2Pay para o
cadastro da subconta — não é o split real de cada corrida (isso é calculado
à parte, por transação, na cobrança via `charge_with_split`, corrida →
subconta do entregador / taxa → conta Jaxegô, ver `docs/integracoes/safe2pay.md`).

## Fix
`app/payments/safe2pay_adapter.py::register_subaccount_full`: `Tax` de `"0"`
para `"0.35"` (mínimo exigido pela Safe2Pay).

## Validado
Testado com o courier real que o usuário estava usando (id 28,
rogergoyerr@gmail.com, já `active` sem subconta): chamada retornou HTTP 200,
`s2p_recipient_id` e `s2p_token` persistidos no banco.

## Pergunta do usuário: dá pra criar a subconta no cadastro em vez de na aprovação do KYC?

Resposta curta: **não é recomendado**. A Safe2Pay valida os dados reais do
CPF+data de nascimento contra a Receita Federal (vimos isso no erro 1343 da
CORRECAO-237 com CPF de teste) — criar a subconta ANTES da aprovação do KYC
significa criar uma conta financeira pra alguém cuja identidade ainda não foi
verificada pelo time. Se depois o admin rejeitar os documentos (foto não bate,
CNH vencida, etc.), você teria uma subconta ativa na Safe2Pay pra uma pessoa
recusada. Manter o gatilho na aprovação do KYC é a ordem correta: primeiro
confirma a pessoa é quem diz ser, depois abre conta pra ela receber dinheiro.
