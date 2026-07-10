# CORRECAO-224 — Entregadores não recebiam ofertas: worker com coluna removida

## Data
2026-07-09

## Erro
```
OperationalError: (1054, "Unknown column 'couriers.max_concurrent' in 'field list'")
  File "/app/app/dispatch/cascade.py", line 110, in build_candidates
```

## Causa
O worker (`jaxego-worker-1`) também roda sem `--reload`. Quando migramos
`couriers.max_concurrent` → `areas.config.max_entregas_simultaneas` (migration 0041)
e atualizamos o modelo `Courier` para remover a coluna, o **worker não foi reiniciado**.

O processo Python em memória usava o ORM `Courier` antigo que ainda definia
`max_concurrent: Mapped[int]`. Toda vez que o SQLAlchemy gerava um `SELECT` de
`Courier`, incluía `couriers.max_concurrent` na query — mas a coluna não existe mais
no banco → `OperationalError 1054` → `dispatch_offer_task` falhava → nenhum
entregador recebia oferta.

## Solução
`docker restart jaxego-worker-1`

## Lição
**Sempre reiniciar AMBOS os containers após mudanças em modelos Python:**
- `docker restart jaxego-api-1`
- `docker restart jaxego-worker-1`

O bind-mount atualiza os arquivos em disco, mas os processos Python precisam reimportar.
