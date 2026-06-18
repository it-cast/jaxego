# Correção 013 — Admin de área sem acesso ao endpoint de configuração da área

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/api/app/areas/admin_router.py` (criado)
- `apps/api/app/api/v1/router.py`
- `apps/web/src/features/admin/area-config/area-config.service.ts`

## Problema

O frontend de configuração da área chamava `GET /v1/areas/{id}` e `PATCH /v1/areas/{id}`, endpoints protegidos por `PlatformAdmin`. O admin de área recebia 403, resultando em "Não conseguimos carregar a configuração. Tente de novo."

## Correção

Criado router dedicado `areas/admin_router.py` com dois endpoints protegidos por `require_role('admin_area')` que lêem o `area_scope` do próprio token (sem parâmetro de path, sem risco de cross-area):

- `GET /v1/admin/area` — retorna a área do admin autenticado
- `PATCH /v1/admin/area/config` — atualiza o config da área com auditoria

O frontend (`area-config.service.ts`) foi atualizado para usar os novos endpoints.
