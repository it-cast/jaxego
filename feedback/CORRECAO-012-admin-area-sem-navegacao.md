# Correção 012 — Admin de área sem navegação lateral

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivo afetado

- `apps/web/src/layouts/admin-shell.component.ts`

## Problema

O `admin-shell` foi criado sem links de navegação — apenas com o toggle de colapso e o theme toggle. O admin de área entrava em `/admin/inicio` e via só um placeholder vazio, sem acesso às páginas disponíveis (config, bairros, disputas, api-keys).

## Correção

Adicionado menu lateral com links para todas as rotas do admin: Painel (`inicio`), Configurações (`config`), Bairros (`bairros`), Disputas (`disputas`) e Chaves de API (`api-keys`). Mesmo padrão visual do `plataforma-shell` com colapso, `routerLinkActive` e tokens semânticos.
