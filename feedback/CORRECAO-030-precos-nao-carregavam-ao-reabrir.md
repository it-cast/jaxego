# Correção 030 — Preços salvos não carregavam ao reabrir a tela de Bairros & Preços

> **Classe:** COD · **Data:** 2026-06-18 · **Relacionada:** Correção 029

---

## Arquivos afetados

- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.service.ts`
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.ts`

## Problema

Após salvar bairros e preços, ao reabrir a tela (F5 ou trocar de tab e voltar) os checkboxes de cobertura apareciam marcados corretamente, mas os campos de preço e o % de retorno ficavam vazios. O `ngOnInit` (Correção 029) carregava catálogo + cobertura mas não carregava o pricing (`GET /v1/couriers/{id}/pricing`).

## Correção

- Adicionado método `getPricing(courierId)` no `CoberturaPrecosService`
- `ngOnInit` agora carrega catálogo, cobertura e pricing em paralelo (`Promise.all`)
- Preços são mapeados por `neighborhood_id` e convertidos para máscara BRL (`maskBrl`)
- `returnPct` é restaurado a partir do primeiro row do pricing
