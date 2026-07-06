---
classe: feature
data: 2026-07-06
arquivos_afetados:
  - apps/api/app/workers/dispatch.py
---

## Problema
Entregadores que ficavam online após a construção da fila de cascade não recebiam ofertas em andamento. A fila era construída uma única vez no início do cascade e não incluía novos entregadores que aparecessem durante a oferta.

## Implementação
Em `advance_offer()`, quando a fila se esgota (`courier_id is None`):

1. Carrega o set `declined` (recusas explícitas + MAX_TIMEOUTS atingido)
2. Chama `build_candidates(excluded_ids=declined)` — inclui entregadores que ficaram online durante o cascade e os que apenas deixaram o tempo expirar sem atingir o limite
3. Se encontrou candidatos → seta nova fila no Redis (`set_candidates`) e avança normalmente com log `dispatch.cascade.refreshed`
4. Se ainda vazio → executa o check original com `excluded_ids=set()` para decidir entre pool (`SEM_RESPOSTA`) ou exhausted

**Proteção de loop infinito**: entregadores que ignoram repetidamente acumulam contagem via `increment_timeout`. Ao atingir `MAX_TIMEOUTS_PER_COURIER` (= 2) são adicionados ao `declined` set e excluídos nas reconstruções seguintes. Sem migration necessária — estado 100% em Redis com TTL de 24h.
