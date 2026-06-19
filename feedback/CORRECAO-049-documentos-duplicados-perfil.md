# Correção 049 — Documentos duplicados no perfil: exibir só o mais recente por tipo

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivo afetado

- `apps/api/app/couriers/service.py`

## Problema

Quando o entregador reenviava um documento reprovado, o backend criava um novo registro na tabela `courier_documents` (mesmo `kind`, novo `id`). O endpoint `GET /v1/couriers/{id}/profile` retornava todos os registros, fazendo o perfil exibir tanto o antigo (rejeitado) quanto o novo (em análise) para o mesmo tipo de documento.

## Correção

`list_courier_documents()` agora ordena por `id DESC` e deduplica por `kind`, retornando apenas o registro mais recente de cada tipo. O entregador vê só o status atual de cada documento, sem histórico de versões anteriores.
