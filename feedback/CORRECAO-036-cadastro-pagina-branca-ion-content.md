# Correção 036 — Página de cadastro do entregador branca: ion-content com height zero

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/features/entregador/cadastro/cadastro.page.html`
- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`

## Problema

A página de cadastro do entregador (`/entregador/cadastro`) renderizava o conteúdo no DOM (confirmado via Playwright: h1, form, stepper presentes), mas visualmente era totalmente branca. O Playwright capturou screenshot em branco enquanto o `innerText` mostrava todo o wizard.

## Causa raiz

A página usava `<ion-content>` como wrapper, mas estava fora do shell (não é child route do `EntregadorShellComponent`). Sem `IonRouterOutlet` no stack de navegação do Ionic, o `<ion-content>` recebe `height: 0` do CSS do Ionic e não exibe nada visualmente.

As páginas dentro do shell (inicio, saldo, perfil, cobertura) não tinham esse problema porque o shell usa `<router-outlet>` do Angular — o `<ion-content>` de cada tab herdava height via flexbox do shell.

## Correção

- `<ion-content>` substituído por `<div class="jx-cad">` com scroll nativo
- `IonContent` removido dos imports do componente
- CSS atualizado: `height: 100dvh; overflow-y: auto; -webkit-overflow-scrolling: touch`
- Verificado via Playwright: screenshot mostra wizard completo renderizado
