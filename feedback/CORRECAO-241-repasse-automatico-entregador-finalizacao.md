# CORRECAO-241 — Repasse automático ao entregador na finalização da entrega

## Data
2026-07-13

## Contrato Safe2Pay confirmado pelo usuário
```
POST https://payment.safe2pay.com.br/v2/InternalTransfer
{
  "IdReceiver": 12345,              // Id numérico da subconta destino
  "IdentificationDebit": "...",     // comentário na conta que perde o valor
  "IdentificationCredit": "...",    // comentário na conta que recebe
  "Amount": 100.00
}
→ { "ResponseDetail": {"Message": "..."}, "HasError": false }  // SEM id de transação
```
Autentica com o token da conta que **perde** dinheiro (ITCAST/SAFE2PAY_TOKEN normal
— NÃO o SAFE2PAY_MARKETPLACE_TOKEN, que é só para criar subconta).

## Fluxo implementado
1. Loja paga PIX → cai 100% na conta ITCAST (já existia).
2. Loja libera despacho → entregadores aceitam (já existia).
3. Entregador avança e finaliza a entrega.
4. **Novo**: ao virar `FINALIZADA`, enfileira job assíncrono (arq) que transfere
   `delivery.price_cents` da ITCAST pra subconta do entregador
   (`courier.s2p_recipient_id`, criada na aprovação do KYC).

Decisões confirmadas com o usuário antes de implementar:
- **Imediato**, sem retenção/escrow de 24h (a tabela `escrow_ledger` existe no
  código mas continua não usada — decisão consciente, registrar como TD se
  quiserem revisitar proteção contra disputa/estorno depois).
- **Assíncrono** (fila arq) — a tela do entregador confirma a entrega na hora,
  sem esperar a resposta da Safe2Pay.

## Arquivos

### Novos
- `app/deliveries/payout.py` — `payout_courier_on_finalize()`: idempotente
  (checa `courier_payout_transaction_id` antes de repetir), degrada
  graciosamente em falha da Safe2Pay (loga `delivery.payout_pending`, entrega
  continua FINALIZADA).
- `app/workers/payout.py` — `payout_courier_task` (entrypoint arq) +
  `enqueue_payout()` (best-effort, mesmo padrão de `enqueue_dispatch`).
- `alembic/versions/0046_delivery_courier_payout.py` — nova coluna
  `deliveries.courier_payout_transaction_id`.

### Alterados
- `app/deliveries/models.py` — campo novo, documentado.
- `app/payments/safe2pay_adapter.py::payout()` — reescrito com o endpoint e
  payload reais (antes era `[ASSUMIDO]`, `/v2/marketplace/transfer`, campo
  `Recipient` string). Como a resposta não traz id de transação, uso a
  `reference` (`dlv_{id}`) como `transaction_id` — é nossa própria chave de
  idempotência, não da Safe2Pay.
- `app/workers/settings.py` — registrado `payout_courier_task` na lista de
  funções do worker.
- `app/proofs/router.py` — `submit_proof` e `submit_reference`: após
  `transition(to_state="FINALIZADA")` + commit, chama `enqueue_payout(delivery.id)`.
- `app/workers/lifecycle.py::finalize_deliveries` — cron de 24h (fallback do
  caminho imediato): mesmo enqueue pra cada entrega finalizada no batch.

### Bug relacionado corrigido de brinde
`app/withdrawals/service.py` (saque manual do entregador) chamava
`payment.payout(recipient=f"courier_{courier_id}", ...)` — uma string
inventada, nunca o Id real da subconta. Como agora `payout()` bate de
verdade no `InternalTransfer` (que exige `IdReceiver` numérico), essa
chamada quebraria (`int("courier_28")` → erro). Corrigido: busca
`courier.s2p_recipient_id` antes de chamar payout; se o entregador ainda não
tem subconta, novo erro `CourierSubaccountMissingError` (422) bloqueia o
saque antes de criar qualquer registro pendente.

## Deploy
Descoberto (de novo) que `--force-recreate` do container reverte
`alembic/versions/` pro estado da imagem (não é bind mount) — todos os
patches manuais de migration da sessão tinham sumido. Recopiei a pasta
`alembic/versions/` inteira (46 arquivos) antes de rodar `alembic upgrade head`.

## Validado
- Import completo de `app.main` e `app.workers.settings` sem erro.
- Worker subiu com `payout_courier_task` na lista das 43 funções registradas.
- Coluna `courier_payout_transaction_id` confirmada via `DESCRIBE deliveries`.
- **NÃO testei uma transferência real** — diferente da criação de subconta
  (que só registra uma conta, sem risco), o `InternalTransfer` MOVE DINHEIRO
  de verdade no ambiente atual (`environment=staging`, sem stub). Só validei
  estrutura/imports; o teste real precisa ser uma entrega de verdade
  finalizada pelo usuário, com atenção ao valor.

## Tech debt aberta
- Sem retry automático se o payout falhar (courier.subaccount tem um 2º
  gatilho natural via validação de MEI; payout não tem — falha fica só
  registrada em log, sem re-tentativa).
- `escrow_ledger` continua implementado mas não usado — se decidirem
  adicionar janela de proteção contra disputa, é onde entra.
