# Correção 027 — Tabs do Ionic não navegam: todas mostram a mesma tela (Início)

> **Classe:** COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/app/app.component.ts` (criado)
- `apps/app/src/main.ts`

## Problema

No app do entregador, clicar em qualquer tab (Ganhos, Bairros, Perfil) não mudava de tela — todas mostravam o conteúdo da tab Início. O `ion-tab-button` com atributo `tab="saldo"` não navegava para a rota correspondente.

## Causa raiz

O `AppComponent` compartilhado (`@jaxego/shared/app/app.component`) usava `<router-outlet />` do Angular padrão. O Ionic Tabs (`IonTabs`) depende do sistema de navegação stack-based do Ionic, que requer `<ion-router-outlet>` e `<ion-app>` no componente raiz. Sem isso, o `IonTabs` não consegue trocar o conteúdo das tabs — o `tab` attribute simplesmente não conecta com o Angular Router.

## Correção

Criado `AppComponent` local para o app em `apps/app/src/app/app.component.ts`:

```typescript
@Component({
  selector: 'jx-root',
  imports: [IonApp, IonRouterOutlet],
  template: `
    <ion-app>
      <ion-router-outlet />
    </ion-app>
  `,
})
```

O `main.ts` foi atualizado para importar o `AppComponent` local em vez do shared. O `apps/web` continua usando o `AppComponent` compartilhado com `<router-outlet>` (não usa Ionic Tabs).
