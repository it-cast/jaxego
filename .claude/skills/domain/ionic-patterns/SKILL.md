# Skill: ionic-patterns

> Padrões Ionic 8 + Angular 19 + Capacitor para apps mobile production-ready: navegação, gestos, keyboard, lifecycle, status bar, safe areas, pull-to-refresh, infinite scroll.
> Categoria: `domain` · 2026-04-18

## Propósito

Padronizar o uso do Ionic 8 no app mobile do {PROJETO} (áreas cliente e profissional). Evita anti-patterns comuns (componentes Angular Material em Ionic, navegação via `router.navigate` quando deveria ser `navCtrl.navigateForward`, quebra de safe area, teclado sobrepondo input).

## Quando usar (triggers)

- Qualquer novo componente ou página em `apps/mobile/`
- Uso de `IonTabs`, `IonSegment`, `IonMenu`, `IonModal`, `IonActionSheet`
- Integração com plugins Capacitor
- Correção de bug mobile
- Code review de PR em `apps/mobile/`

## Quando NÃO usar

- Admin Angular (`apps/admin/`) → use `angular-material-patterns`
- Formulário BR → use `brazilian-forms` em conjunto
- Upload de arquivo → use `file-upload-ux` em conjunto

---

## 1. Standalone components em Ionic 8

Ionic 8 aboliu `@NgModule`. **Sempre** standalone.

```typescript
import { IonHeader, IonToolbar, IonTitle, IonContent, IonButton } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { home, search, person } from 'ionicons/icons';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [IonHeader, IonToolbar, IonTitle, IonContent, IonButton],
  template: `
    <ion-header [translucent]="true">
      <ion-toolbar>
        <ion-title>Home</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content [fullscreen]="true">
      <!-- ... -->
    </ion-content>
  `,
})
export class HomePage {
  constructor() {
    addIcons({ home, search, person });
  }
}
```

### Por que importar ícones assim?

- Ionic 8 usa lazy-loading de ícones
- `addIcons()` registra apenas os que você usa → bundle menor
- `<ion-icon name="home" />` só funciona se registrado

---

## 2. Navegação: `NavController` vs `Router`

**Regra:** use `NavController` para navegação entre páginas do mesmo "stack". Use `Router` para navegação global (como deep link ou logout).

```typescript
import { NavController } from '@ionic/angular/standalone';

@Component({ /* ... */ })
export class ProfessionalListPage {
  private nav = inject(NavController);

  goToDetail(id: string) {
    // ✅ Anima forward (direita pra esquerda no iOS)
    this.nav.navigateForward(['/client/professional', id]);
  }

  goBack() {
    // ✅ Anima back (esquerda pra direita)
    this.nav.navigateBack(['/client/search']);
  }

  goToTab() {
    // ✅ Sem animação (mudança de tab)
    this.nav.navigateRoot(['/client/tabs/home']);
  }
}
```

**Nunca** use `this.router.navigate()` entre páginas — quebra animações nativas.

---

## 3. Lifecycle hooks (Ionic ≠ Angular)

Páginas Ionic têm hooks específicos **além** dos Angular:

```typescript
import { ViewWillEnter, ViewDidEnter, ViewWillLeave } from '@ionic/angular';

export class ProfilePage implements ViewWillEnter, ViewDidEnter, ViewWillLeave {

  ionViewWillEnter() {
    // Toda vez que a página ENTRA em view (inclusive voltando no stack)
    // Use para recarregar dados, registrar listeners
    this.loadProfile();
  }

  ionViewDidEnter() {
    // Após animação de entrada completar
    // Use para focus em input, iniciar analytics
  }

  ionViewWillLeave() {
    // Antes de sair
    // Use para unsubscribe, cleanup
  }
}
```

**`ngOnInit` não basta** — ele só dispara uma vez, mas páginas Ionic ficam em cache e podem ser revisitadas. Use `ionViewWillEnter` para dados que precisam atualizar.

---

## 4. Tabs pattern

```typescript
// apps/mobile/src/app/client/tabs.page.ts
@Component({
  standalone: true,
  imports: [IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel],
  template: `
    <ion-tabs>
      <ion-tab-bar slot="bottom">
        <ion-tab-button tab="home">
          <ion-icon name="home" />
          <ion-label>Home</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="search">
          <ion-icon name="search" />
          <ion-label>Busca</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="orders">
          <ion-icon name="list" />
          <ion-label>Pedidos</ion-label>
          <ion-badge *ngIf="unreadOrders() > 0">{{ unreadOrders() }}</ion-badge>
        </ion-tab-button>
        <ion-tab-button tab="messages">
          <ion-icon name="chatbubbles" />
          <ion-label>Mensagens</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="profile">
          <ion-icon name="person" />
          <ion-label>Perfil</ion-label>
        </ion-tab-button>
      </ion-tab-bar>
    </ion-tabs>
  `,
})
export class ClientTabsPage {
  unreadOrders = inject(OrdersService).unreadCount;
}
```

```typescript
// Routes
export const clientTabsRoutes: Routes = [
  {
    path: '',
    component: ClientTabsPage,
    children: [
      { path: 'home', loadComponent: () => import('./home/home.page').then(m => m.HomePage) },
      { path: 'search', loadComponent: () => import('./search/search.page').then(m => m.SearchPage) },
      // ...
      { path: '', redirectTo: 'home', pathMatch: 'full' },
    ],
  },
];
```

---

## 5. Segment (filtro cliente/profissional na tela de login)

Padrão usado no LoginPage do {PROJETO}:

```typescript
@Component({
  standalone: true,
  imports: [IonSegment, IonSegmentButton, IonLabel, ReactiveFormsModule],
  template: `
    <ion-segment [value]="userType()" (ionChange)="onTypeChange($event)">
      <ion-segment-button value="client">
        <ion-label>Sou cliente</ion-label>
      </ion-segment-button>
      <ion-segment-button value="professional">
        <ion-label>Sou profissional</ion-label>
      </ion-segment-button>
    </ion-segment>
  `,
})
export class LoginPage {
  userType = signal<'client' | 'professional'>('client');

  onTypeChange(e: CustomEvent) {
    this.userType.set(e.detail.value);
  }
}
```

---

## 6. Pull-to-refresh e Infinite Scroll

```html
<ion-content>
  <ion-refresher slot="fixed" (ionRefresh)="onRefresh($event)">
    <ion-refresher-content />
  </ion-refresher>

  @for (item of items(); track item.id) {
    <ion-item>{{ item.title }}</ion-item>
  }

  <ion-infinite-scroll (ionInfinite)="onLoadMore($event)">
    <ion-infinite-scroll-content loadingText="Carregando mais…" />
  </ion-infinite-scroll>
</ion-content>
```

```typescript
async onRefresh(event: CustomEvent) {
  await this.reload();
  (event.target as HTMLIonRefresherElement).complete();
}

async onLoadMore(event: CustomEvent) {
  await this.loadNextPage();
  const target = event.target as HTMLIonInfiniteScrollElement;
  target.complete();
  if (this.isLastPage()) target.disabled = true;
}
```

---

## 7. Safe Areas (notch, home indicator)

Ionic cuida automaticamente **se** você usar `ion-header` e `ion-footer`. Para conteúdo custom:

```scss
ion-content {
  --padding-top: var(--ion-safe-area-top, 0);
  --padding-bottom: var(--ion-safe-area-bottom, 0);
}

.fab-custom {
  bottom: calc(16px + var(--ion-safe-area-bottom, 0));
}
```

---

## 8. Keyboard handling

```typescript
import { Keyboard } from '@capacitor/keyboard';

// Ajustar scroll quando input focar e teclado aparecer
ionViewWillEnter() {
  Keyboard.addListener('keyboardWillShow', info => {
    this.keyboardHeight.set(info.keyboardHeight);
  });
  Keyboard.addListener('keyboardWillHide', () => {
    this.keyboardHeight.set(0);
  });
}

ionViewWillLeave() {
  Keyboard.removeAllListeners();
}
```

**iOS:** tela não rola automaticamente — adicione `scroll-padding-bottom` no `ion-content`.

---

## 9. Back button (hardware Android)

```typescript
import { App } from '@capacitor/app';

constructor() {
  App.addListener('backButton', async ({ canGoBack }) => {
    if (!canGoBack) {
      // Mostrar confirmação de saída
      const confirm = await this.alert.create({
        header: 'Sair do app?',
        buttons: [
          { text: 'Cancelar', role: 'cancel' },
          { text: 'Sair', handler: () => App.exitApp() },
        ],
      });
      await confirm.present();
    } else {
      this.nav.back();
    }
  });
}
```

---

## 10. Status Bar

```typescript
// app.component.ts
import { StatusBar, Style } from '@capacitor/status-bar';

async ngOnInit() {
  if (Capacitor.isNativePlatform()) {
    await StatusBar.setStyle({ style: Style.Light });  // ícones brancos
    await StatusBar.setBackgroundColor({ color: '#1565C0' });  // primary do {PROJETO}
  }
}
```

---

## Anti-patterns

1. ❌ **Usar `@angular/material`** dentro de componente Ionic mobile — quebra look-and-feel
2. ❌ **`router.navigate()`** entre páginas → sem animação nativa, use `NavController`
3. ❌ **`ngOnInit` para recarregar dados** em página que fica em cache → use `ionViewWillEnter`
4. ❌ **Ignorar retorno `cancelled` de Capacitor** (camera, permissions) → crash
5. ❌ **Hardcoded `16px` em bottom sem safe-area** → cobre pelo home indicator do iPhone
6. ❌ **`<button>`** em vez de `<ion-button>` em tela mobile → não tem ripple/touch feedback
7. ❌ **Não registrar ícone com `addIcons()`** → ícone não aparece silenciosamente
8. ❌ **Fazer `ion-input type="number"`** para CPF/CEP → remove zeros à esquerda
9. ❌ **Esquecer `(event.target as HTMLIonRefresherElement).complete()`** → refresher trava
10. ❌ **Listener Capacitor sem remove** em `ionViewWillLeave` → memory leak

---

## Checklist de review

- [ ] Componente é standalone, não usa NgModule
- [ ] Ícones registrados via `addIcons({ ... })`
- [ ] Navegação via `NavController`, não `Router.navigate`
- [ ] `ionViewWillEnter` para dados que atualizam ao revisitar
- [ ] Pull-to-refresh tem `.complete()` no final
- [ ] Infinite scroll desabilita ao final
- [ ] Safe area respeitada em FABs e componentes com `position: fixed`
- [ ] Listeners Capacitor removidos em `ionViewWillLeave`
- [ ] `ion-button` em vez de `<button>` em botões de ação
- [ ] Cancel de camera/picker tratado graciosamente
- [ ] Status bar configurada no startup

<!-- Skill aplicada: toda página em apps/mobile/ -->
