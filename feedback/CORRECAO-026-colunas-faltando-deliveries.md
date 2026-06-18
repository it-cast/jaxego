# Correção 026 — Colunas faltando na tabela deliveries: 500 em endpoints do entregador

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/api/app/deliveries/models.py` (model já tinha as colunas)
- Tabela `deliveries` no MySQL (faltavam as colunas)

## Problema

Os endpoints `GET /v1/couriers/{id}/deliveries` e `GET /v1/couriers/{id}/deliveries/active` retornavam 500 Internal Server Error. O model SQLAlchemy (`Delivery`) definia as colunas `weight_g`, `length_cm`, `width_cm` e `height_cm` (package size/weight — MG-1), mas essas colunas não existiam na tabela real do banco. A migration que as adicionaria não foi executada.

## Erro no log

```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)
(1054, "Unknown column 'deliveries.weight_g' in 'field list'")
```

## Correção

Colunas adicionadas via ALTER TABLE:

```sql
ALTER TABLE deliveries
  ADD COLUMN weight_g INT NULL,
  ADD COLUMN length_cm INT NULL,
  ADD COLUMN width_cm INT NULL,
  ADD COLUMN height_cm INT NULL;
```

## Nota

O `GET /v1/couriers/{id}/score` retorna 404 ("Score ainda não calculado") — comportamento esperado quando o courier não tem entregas finalizadas. O frontend trata com empty state.
