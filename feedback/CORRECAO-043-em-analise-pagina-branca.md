# Correção 043 — Página "Em análise" branca após cadastro: mesmo problema do ion-content

> **Classe:** COD · **Data:** 2026-06-18 · **Relacionada:** Correção 036

---

## Arquivo afetado

- `apps/app/src/features/entregador/cadastro/em-analise.component.ts`

## Problema

Após concluir o cadastro, a página `/entregador/cadastro/em-analise` ficava branca. Mesma causa da Correção 036: `<ion-content>` fora do shell Ionic recebe `height: 0`.

## Correção

`<ion-content>` substituído por `<div class="jx-analise">` com `height: 100dvh`, flexbox centralizado, scroll nativo. `IonContent` removido dos imports.
