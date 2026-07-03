# CORRECAO-192 — Campos Complemento e Referência na nova entrega

## Solicitação
Adicionar campos de complemento e referência no formulário de nova entrega, com coluna no banco.

## O que existia
- `dropoff_complement` já estava no banco (migration 0006) e no service, mas **não no formulário**
- `dropoff_reference` não existia em nenhuma camada

## Mudanças

### Backend
- `0035_delivery_dropoff_reference.py` — migration que adiciona `dropoff_reference VARCHAR(255) NULL` à tabela `deliveries`
- `models.py` — `dropoff_reference: Mapped[str | None]`
- `schemas.py` — `dropoff_reference` adicionado em `CreateDeliveryBody`, `DeliveryOut` e `CourierDeliveryOut`
- `service.py` — `dropoff_reference=body.dropoff_reference` na criação do delivery

### Frontend
- `delivery.models.ts` — `dropoff_reference?: string | null` em `CreateDeliveryRequest`
- `nova-entrega.page.ts` — `dropoff_complement` e `dropoff_reference` adicionados ao `FormGroup`, mapeados no `submit()`
- `nova-entrega.page.html` — dois campos `jx-field` após "Número": Complemento (opcional) e Referência (opcional)

## Observação
As migrations 0031-0034 (zonas) também foram copiadas para o container pois o volume mount cobre apenas `app/app/`, não `alembic/`.
