# Correção 023 — Painel do admin de área era placeholder: implementação completa

> **Classe:** COD/PROC · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/features/admin/inicio.page.ts`
- `apps/web/src/features/admin/inicio.page.html` (criado)
- `apps/web/src/features/admin/inicio.page.scss` (criado)

## Problema

A tela `/admin/inicio` (painel do admin de área) exibia apenas um placeholder vazio — sem dados reais.

## Implementação

Painel espelhando `a-dash` do protótipo:

- Grid de 4 KPIs (entregas hoje, online agora, mediana de aceite, taxas hoje) — valores mostrados como `'—'` até endpoint de stats ser adicionado à API
- Lista de filas que precisam de ação: disputas de pagamento direto (contagem real via `GovernancaService.listDisputes()`) e recursos de suspensão (via `listAppeals(true)`); os demais exibem `'…'` enquanto carregam e `0` em caso de erro
- Badges de contagem são `<a [routerLink]>` quando há rota definida ou `<span>` quando não (aguardando implementação futura)
- Grid 4 colunas responsivo (colapsa para 2 colunas abaixo de 720px)
