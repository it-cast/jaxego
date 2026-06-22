# Correção 073 — Função de re-despacho de entregas presas em CRIADA

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/api/app/workers/dispatch.py`

## Problema

Quando uma entrega era criada sem nenhum entregador online, o dispatch rodava uma única vez, não encontrava candidatos, e a entrega ficava presa em `CRIADA` para sempre. Mesmo que um entregador ficasse online depois, a entrega nunca era re-despachada.

## Implementação

Criada a função `redispatch_stale_deliveries(ctx)` que:
1. Busca todas as entregas em estado `CRIADA`
2. Verifica se cada uma tem oferta ativa no Redis ou fila de candidatos
3. Se não tem nenhuma das duas (cascata esgotada ou nunca iniciada), re-enfileira o job `dispatch_offer_task`
4. Retorna a quantidade de entregas re-despachadas
5. Loga cada re-despacho e o total do sweep

A função está pronta para ser registrada como cron no `workers/settings.py` (ex: a cada 5 minutos). Não foi registrada automaticamente — o operador decide quando ativar.
