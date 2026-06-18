# Correção 029 — Tela de Bairros & Preços não exibia os bairros cadastrados pelo admin

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.service.ts`
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.ts`

## Problema

A tela "Bairros & preços" do entregador não exibia nenhum bairro, mesmo com bairros cadastrados pelo admin da área (Bexiga, Centro). O signal `items` começava vazio (`signal<CoverageItem[]>([])`) e o `ngOnInit` só chamava `getCoverage()` (que retorna a cobertura **existente** do entregador), mas nunca buscava o **catálogo de bairros da área**. O comentário no código reconhecia isso: *"The neighborhood list comes from the area catalog (injected once that resolver lands)."*

## Correção

- Adicionado método `catalog()` no `CoberturaPrecosService` que chama `GET /v1/neighborhoods/catalog` (endpoint já existia — Correção 017)
- `ngOnInit` agora carrega catálogo e cobertura em paralelo (`Promise.all`)
- `items` é populado com todos os bairros da área, marcando os que o entregador já cobre
