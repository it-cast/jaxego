# Correção 017 — Listagem de bairros vazia no formulário de nova entrega

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/api/app/neighborhoods/router.py`
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts`

## Problema

O frontend chamava `GET /v1/neighborhoods` para popular o select de bairro no formulário de nova entrega. Esse endpoint exige `admin_area` — a loja recebia 403, o `catch` silencioso definia `neighborhoods = []` e o campo aparecia vazio.

## Correção

Adicionado endpoint `GET /v1/neighborhoods/catalog` no router de bairros, acessível por qualquer usuário autenticado com `area_scope` definido (merchants, couriers, area admins). Retorna os bairros ativos da área do token. O frontend foi atualizado para chamar `/v1/neighborhoods/catalog`.
