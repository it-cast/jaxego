# CORRECAO-242 — Fix: repasse ao entregador faltando no endpoint finalize-no-proof

## Data
2026-07-13

## Sintoma
Usuário testou o fluxo completo (loja paga PIX → entregador aceita → finaliza)
e o valor não chegou na subconta do entregador, apesar da CORRECAO-241 ter
implementado o repasse automático.

## Causa raiz
A pesquisa que embasou a CORRECAO-241 mapeou 3 caminhos de finalização
(`proofs/router.py::submit_proof`, `submit_reference`, e o cron de 24h em
`workers/lifecycle.py`) — mas existe um **4º caminho** não encontrado na
varredura anterior: `POST /v1/couriers/{id}/deliveries/{id}/finalize-no-proof`
(`app/couriers/router.py:598`), usado quando a entrega tem
`proof_method="none"` (área não exige comprovação). Foi exatamente esse
endpoint que processou a entrega de teste do usuário (confirmado nos logs:
`endpoint: "/v1/couriers/29/deliveries/107/finalize-no-proof"`).

## Fix
Adicionado `enqueue_payout(delivery.id)` após o `session.commit()` em
`finalize_no_proof` — mesmo padrão dos outros 3 call sites.

## Verificação de completude
```
grep -rn 'to_state="FINALIZADA"' app --include="*.py"
```
Confirma exatamente 4 ocorrências, todas agora com o enqueue:
- `app/couriers/router.py:616` (finalize_no_proof) — **corrigido agora**
- `app/workers/lifecycle.py:84` (cron 24h)
- `app/proofs/router.py:105` (submit_proof)
- `app/proofs/router.py:154` (submit_reference)

## Entrega de teste (id 107)
Não reprocessada. O usuário já estornou o PIX pago pela loja antes de eu
diagnosticar o problema — repassar agora criaria uma saída de caixa da ITCAST
sem entrada correspondente. Deixada como está (courier_payout_transaction_id
permanece NULL).

## Achado secundário (não corrigido, fora de escopo)
O webhook de estorno da Safe2Pay (`event_status: "6"`) chega e é logado em
`payments/webhooks_router.py::_process_event`, mas não atualiza
`platform_charges.status` — a cobrança fica marcada `paid` mesmo depois do
estorno confirmado pela Safe2Pay. `platform_charges` id 33 (delivery 107)
confirma: `status=paid` apesar do estorno já ter sido feito. Vale corrigir se
o estorno for um fluxo usado com frequência (hoje não há reconciliação
automática desse caso).
