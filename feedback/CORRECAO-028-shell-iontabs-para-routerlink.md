# Correção 028 — Shell do entregador trocado de IonTabs para tab bar manual com routerLink

> **Classe:** COD · **Data:** 2026-06-18 · **Relacionada:** Correção 027

---

## Arquivos afetados

- `apps/app/src/layouts/entregador-shell.component.ts` (reescrito)
- `apps/app/src/app/app.component.ts` (revertido para `<router-outlet>` padrão)

## Problema

Após a Correção 027 (`<ion-app>` + `<ion-router-outlet>`), as tabs continuavam não navegando — cada troca de página exigia Ctrl+F5 (hard refresh). O conteúdo da rota não renderizava até um reload completo do browser.

Tentativas que falharam:
1. `IonTabs` com atributo `tab` sozinho → não navegava
2. `IonTabs` com `routerLink` adicionado → não navegava
3. `IonTabs` com `href` → não navegava
4. `AppComponent` com `<ion-router-outlet>` → login parou de funcionar (na verdade era senha errada, mas a navegação entre páginas continuava exigindo hard refresh)
5. `AppComponent` com `<ion-app><router-outlet></ion-app>` → mesma coisa

## Causa raiz

O `IonTabs` do Ionic 8 em modo Angular standalone não conecta corretamente com o Angular Router quando o `AppComponent` raiz usa `<router-outlet>` do Angular padrão. O sistema de navegação stack-based do Ionic (`IonRouterOutlet`) não é compatível com o setup do monorepo onde o `AppComponent` é compartilhado entre web (sem Ionic) e app (com Ionic).

## Correção

Shell reescrito sem nenhum componente de navegação do Ionic:
- Removido: `IonTabs`, `IonTabBar`, `IonTabButton`, `IonLabel`
- Adicionado: `RouterOutlet`, `RouterLink`, `RouterLinkActive` do Angular
- Tab bar agora é `<nav>` com `<a routerLink="..." routerLinkActive="jx-tab--active">` — mesma mecânica de navegação do `apps/web`
- Content area usa `<router-outlet />` padrão do Angular
- Layout via flexbox: content (flex:1, overflow-y:auto) + tabbar fixa no fundo com `safe-area-inset-bottom`

`AppComponent` revertido para `<router-outlet />` simples (sem `<ion-app>`), idêntico ao shared.
