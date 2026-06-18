# Correção 019 — Página de CRUD de Áreas no admin de plataforma

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/features/admin-plataforma/areas.page.ts` (criado)
- `apps/web/src/features/admin-plataforma/areas.page.html` (criado)
- `apps/web/src/features/admin-plataforma/areas.page.scss` (criado)
- `apps/web/src/features/admin-plataforma/platform-admin.service.ts`
- `apps/web/src/layouts/plataforma-shell.component.ts`
- `apps/web/src/app/app.routes.ts`

## Problema

As áreas existiam apenas como KPIs na tela de visão geral. Não havia página dedicada para gerenciar (criar, editar, arquivar) as áreas de operação.

## Implementação

- Nova rota `/plataforma/areas` com link "Áreas" no menu lateral (ícone `faCity`)
- Listagem com filtro client-side por nome ou codename
- Tabela com colunas: ID, Codename, Nome, Status, Data, Ações
- Drawer lateral para Add (campos: codename + nome) e Edit (apenas nome — codename é imutável)
- Archive (soft-delete) com confirmação inline
- 4 métodos adicionados ao `PlatformAdminService`: `listAreas`, `createArea`, `updateArea`, `archiveArea`
