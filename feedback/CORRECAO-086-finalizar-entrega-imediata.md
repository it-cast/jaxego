# Correção 086 — Entrega finalizada imediatamente após comprovação

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/api/app/proofs/router.py`

## Problema

Após o entregador comprovar a entrega (foto ou número do pedido), a entrega ficava em estado `ENTREGUE` por até 24h aguardando o cron `finalize_deliveries`. No M1 com pagamento direto, essa janela não tem utilidade — o dinheiro já foi trocado em mãos.

## Correção

- Nos endpoints `submit_proof` (foto) e `submit_reference` (número do pedido), após a transição para `ENTREGUE`, executa imediatamente `transition(..., to_state="FINALIZADA", reason="immediate_finalize")`
- A entrega vai direto de `ENTREGUE` para `FINALIZADA` na mesma request, sem esperar o cron
- O cron `finalize_deliveries` continua existindo como safety net para entregas que por algum motivo não finalizaram inline
