# Correção 060 — Status online do entregador não persistia após F5

> **Classe:** COD · **Data:** 2026-06-19

---

## Arquivos afetados

- `apps/api/app/couriers/schemas.py` (adicionado `is_online` ao `CourierProfileOut`)
- `apps/api/app/couriers/router.py` (profile retorna `is_online`)
- `apps/app/src/features/entregador/entregador.service.ts` (adicionado `is_online` à interface)
- `apps/app/src/features/entregador/inicio.page.ts` (carrega `is_online` do profile no init)

## Problema

O entregador ativava o toggle "Online", mas ao dar F5 ou trocar de tab e voltar, o toggle voltava para "Offline". O PATCH `/v1/couriers/{id}/availability` salvava `is_online=true` no banco, mas o `ngOnInit` da home sempre inicializava `online = signal(false)` sem consultar o valor salvo.

## Correção

- `CourierProfileOut` agora inclui `is_online`
- `ngOnInit` da home carrega o profile em paralelo e seta `online` com o valor do banco
- Após F5, o toggle reflete o estado real do entregador
