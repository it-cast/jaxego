# Correção 052 — Cidades no cadastro do entregador eram hardcoded (Pádua/Itaocara)

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/api/app/areas/router.py` (adicionado `GET /v1/areas/public`)
- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`

## Problema

O select "Cidade onde vai entregar" no cadastro do entregador tinha valores fixos: Pádua (completa) e Itaocara (simples). As áreas reais cadastradas no admin (São Paulo, Rio de Janeiro) não apareciam.

## Correção

**Backend:**
- Novo endpoint público `GET /v1/areas/public` — sem autenticação, retorna apenas `id`, `name` e `kyc_level` das áreas ativas (sem config completo, sem dados sensíveis)
- `kyc_level` extraído do campo JSON `config` da área (default `simples`)

**Frontend:**
- Array hardcoded removido; `areas` signal começa vazio
- `ngOnInit` chama `GET /v1/areas/public` e popula o signal
- Se falhar, select fica vazio (sem erro bloqueante)
