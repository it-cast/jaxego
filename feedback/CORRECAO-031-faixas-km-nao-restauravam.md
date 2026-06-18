# Correção 031 — Faixas de km e modo não restauravam ao recarregar Bairros & Preços

> **Classe:** COD · **Data:** 2026-06-18 · **Relacionada:** Correção 030

---

## Arquivos afetados

- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.ts`
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.service.ts`

## Problema

Quando o entregador salvava preços no modo "Por km" (ex: até 1km = R$1, até 5km = R$5), ao recarregar a página o modo voltava para "Por bairro" e as faixas de km ficavam vazias. O `ngOnInit` (Correção 030) restaurava preços por bairro e `returnPct`, mas não restaurava o `mode` nem as `kmBands`.

## Correção

- `PricingRow` agora inclui campo `mode` (que o backend já retorna)
- `ngOnInit` detecta o `mode` salvo e seta `this.mode.set(savedMode)`
- Se `mode === 'km'`, popula `this.kmBands` com as faixas salvas (up_to_km + price mascarado)
