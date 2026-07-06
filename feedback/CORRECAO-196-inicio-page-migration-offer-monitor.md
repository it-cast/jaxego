---
classe: refactor
data: 2026-07-06
arquivos_afetados:
  - apps/app/src/features/entregador/inicio.page.ts
---

## Problema
`inicio.page.ts` ainda continha código legado de polling de ofertas (`pollOffer`, `acceptOffer`, `declineOffer`, signals `offer`/`offerResult`/`processing`, `setInterval`) após a migração para `OfferMonitorService`. Também havia um bloco `catch` órfão de um método removido, causando erro de compilação.

## Implementação
- Removido `implements OnDestroy` da declaração da classe
- Removido `private readonly offers = inject(OfferService)`
- Removidos signals `offer`, `offerResult`, `processing` e `pollHandle`
- Removidos métodos `ngOnDestroy`, `pollOffer`, `acceptOffer`, `declineOffer`
- Removido `setInterval` do `ngOnInit`
- Removido bloco `catch` órfão (resto do `pollOffer` cortado pela edição anterior)
- `state()` computed atualizado para usar `this.monitor.offer()` via `OfferMonitorService` já injetado
- Corrigida anotação de tipo inline em `extract.filter()` que conflitava com `ExtractEntry.at: string | null`
