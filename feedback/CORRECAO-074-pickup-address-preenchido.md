# Correção 074 — Endereço de coleta pré-preenchido com nome da loja

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend (API)

- `apps/api/app/auth/schemas.py` — campo `trade_name` adicionado ao `MeResponse`
- `apps/api/app/auth/service.py` — `resolve_surface` popula `trade_name` para merchants

### Frontend

- `packages/shared/src/core/auth/auth.models.ts` — campo `trade_name` na interface `Me`
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts` — pré-preenche `pickup_address` com `trade_name` do `AuthService.me()`

## Problema

Na página de nova entrega, o campo "Endereço de coleta" vinha vazio. O lojista precisava digitar o endereço toda vez, sendo que na maioria dos casos a coleta é na própria loja.

## Correção

- `MeResponse` agora inclui `trade_name` para usuários do tipo loja
- No construtor de `NovaEntregaPage`, se `me().trade_name` existe, preenche o `pickup_address` automaticamente
- O lojista pode alterar o valor se a coleta for em outro endereço
