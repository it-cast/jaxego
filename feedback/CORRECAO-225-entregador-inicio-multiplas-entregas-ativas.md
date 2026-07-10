# CORRECAO-225 — Início do entregador exibia só a última entrega ativa

## Data
2026-07-09

## Problema
`/entregador/inicio` exibia apenas UM card de "Entrega em andamento" mesmo quando
o entregador tinha múltiplas entregas ACEITA/COLETADA simultâneas
(recurso habilitado por `max_entregas_simultaneas > 1`).

## Causa raiz
- Signal `active = signal<CourierDelivery | null>(null)` guardava uma única entrega
- `ngOnInit` chamava `svc.activeDelivery(id)` → endpoint `/deliveries/active` com `.limit(1)`
- Template `@case ('busy')` renderizava um card único usando `active()!`
- `state()` computed: `if (this.active()) return 'busy'` — só verificava se havia alguma

## Solução

### Backend — `apps/api/app/deliveries/service.py`
Nova função `get_courier_active_deliveries()` que retorna TODAS as entregas ativas
sem LIMIT 1, ordenadas por `accepted_at DESC`.

### Backend — `apps/api/app/couriers/router.py`
Novo endpoint:
```
GET /v1/couriers/{courier_id}/deliveries/active-list → list[CourierDeliveryOut]
```
Declarado ANTES do `/{courier_id}/deliveries` para evitar conflito de rota.

### Frontend — `apps/app/src/features/entregador/entregador.service.ts`
Novo método `activeDeliveries(courierId)` chamando o endpoint `/active-list`.

### Frontend — `apps/app/src/features/entregador/inicio.page.ts`
- Signal: `active: CourierDelivery | null` → `actives: CourierDelivery[]`
- `state()`: `this.actives().length > 0` em vez de `this.active()`
- `ngOnInit`: `activeDeliveries(id)` em vez de `activeDelivery(id)`
- Template `@case ('busy')`: `@for (d of actives(); track d.id)` — um card por entrega
- `goActive(deliveryId: number)`: navega com `?deliveryId=N`

### Frontend — `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts`
- Injeta `ActivatedRoute`
- Em `reload()`: se `?deliveryId` presente → `getDelivery(courierId, deliveryId)`;
  senão → `activeDelivery(courierId)` (compatibilidade retroativa para outros fluxos)

## Verificação
- Endpoint `/active-list` confirmado registrado via `app.routes`
- Container reiniciado após mudanças Python: `docker restart jaxego-api-1`

## Lição
Ao habilitar `max_entregas_simultaneas > 1`, toda tela que mostra "entrega ativa"
precisa ser revisada para suportar arrays, não scalars.
