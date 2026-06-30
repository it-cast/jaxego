# CORRECAO-167 — Nome do entregador na página de detalhe da entrega

## Página
`http://localhost:4200/loja/entregas/:id`

## Arquivos alterados
- `apps/api/app/deliveries/schemas.py` — campo `courier_name: str | None = None` em `DeliveryOut`
- `apps/api/app/deliveries/router.py` — `get_delivery` busca `Courier.full_name` quando `courier_id` presente; `_delivery_out` aceita e repassa `courier_name`
- `packages/shared/src/shared/models/delivery.models.ts` — `courier_name: string | null` em `DeliveryListItem`
- `apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.ts` — exibe `dt/dd "Entregador"` no painel lateral quando `courier_id` não é null

## Comportamento
- Entrega sem entregador (estado CRIADA): campo "Entregador" não aparece
- Entrega com entregador (ACEITA, COLETADA, ENTREGUE, FINALIZADA, etc.): exibe o nome completo

## Requer rebuild do container API
```
docker compose -f infra/docker-compose.yml build api && docker compose up -d api
```
