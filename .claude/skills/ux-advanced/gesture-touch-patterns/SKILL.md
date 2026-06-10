---
name: gesture-touch-patterns
description: Padrões de gestos e interação touch no {PROJETO} com Ionic 8 + Capacitor. Cobre swipe-to-action em listas, pull-to-refresh, long press, bottom sheet, haptic feedback e touch targets 44×44px. Use em qualquer tela com listas ou interações touch.
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Gesture & Touch Patterns

> No mobile, os gestos são atalhos invisíveis. Quando funcionam bem, o usuário nem percebe. Quando falham, ele desinstala.

---

## 1. Quando usar

- Listas com ações (orçamentos, serviços, mensagens)
- Telas com pull-to-refresh (home, orders, quotes)
- Items que podem ser deletados ou arquivados (swipe)
- Ações contextual com long press
- Modais que sobem da base da tela (bottom sheet)

---

## 2. Pull-to-refresh (padrão em todas as listas)

```html
<ion-content>
  <ion-refresher slot="fixed" (ionRefresh)="refresh($event)">
    <ion-refresher-content
      pullingIcon="chevron-down-circle-outline"
      pullingText="Puxe para atualizar"
      refreshingSpinner="crescent"
      refreshingText="Atualizando...">
    </ion-refresher-content>
  </ion-refresher>

  <!-- Conteúdo da lista -->
</ion-content>
```

```typescript
async refresh(event: RefresherCustomEvent): Promise<void> {
  try {
    await this.loadData();
  } finally {
    event.target.complete();
  }
}
```

**Regra:** toda lista de dados dinâmicos deve ter pull-to-refresh. Sem exceção.

---

## 3. Swipe-to-action em listas

```html
<!-- IonItemSliding — swipe revela ações -->
<ion-list>
  @for (item of items(); track item.id) {
    <ion-item-sliding>
      <!-- Ação esquerda (swipe right) — ação positiva -->
      <ion-item-options side="start" (ionSwipe)="archive(item)">
        <ion-item-option color="primary" expandable (click)="archive(item)">
          <ion-icon slot="icon-only" name="archive-outline"></ion-icon>
        </ion-item-option>
      </ion-item-options>

      <!-- Item principal -->
      <ion-item [routerLink]="['/detail', item.id]" detail>
        <!-- conteúdo -->
      </ion-item>

      <!-- Ação direita (swipe left) — ação destrutiva -->
      <ion-item-options side="end" (ionSwipe)="confirmDelete(item)">
        <ion-item-option color="danger" expandable (click)="confirmDelete(item)">
          <ion-icon slot="icon-only" name="trash-outline"></ion-icon>
        </ion-item-option>
      </ion-item-options>
    </ion-item-sliding>
  }
</ion-list>
```

**Regras:**
- Esquerda (swipe right) → ação positiva (arquivar, marcar lido)
- Direita (swipe left) → ação destrutiva (excluir)
- Ações destrutivas → AlertController de confirmação ANTES de executar
- `expandable` = swipe completo executa sem precisar tocar no botão

---

## 4. Haptic feedback (Capacitor)

```typescript
import { Haptics, ImpactStyle, NotificationType } from '@capacitor/haptics';

// Feedback leve — tap em botões, seleção
await Haptics.impact({ style: ImpactStyle.Light });

// Feedback médio — confirmação de ação
await Haptics.impact({ style: ImpactStyle.Medium });

// Feedback forte — ação destrutiva
await Haptics.impact({ style: ImpactStyle.Heavy });

// Notificação de sucesso
await Haptics.notification({ type: NotificationType.Success });

// Notificação de erro
await Haptics.notification({ type: NotificationType.Error });

// Vibração de aviso
await Haptics.notification({ type: NotificationType.Warning });
```

**Quando usar:**
| Ação | Haptic |
|------|--------|
| Tap em botão CTA | `Light` |
| Enviar mensagem/proposta | `Medium` |
| Pagamento confirmado | `Success` |
| Erro de validação | `Error` |
| Deletar item | `Heavy` → depois `Error` |
| Long press ativado | `Medium` |
| Pull-to-refresh trigger | `Light` (Ionic faz automaticamente) |

---

## 5. Long press (ação contextual)

```typescript
// Usar IonGesture via GestureController
import { GestureController } from '@ionic/angular';

private gestureCtrl = inject(GestureController);
private longPressTimeout: ReturnType<typeof setTimeout> | null = null;

setupLongPress(element: HTMLElement, callback: () => void): void {
  const gesture = this.gestureCtrl.create({
    el: element,
    threshold: 0,
    gestureName: 'long-press',
    onStart: () => {
      this.longPressTimeout = setTimeout(async () => {
        await Haptics.impact({ style: ImpactStyle.Medium });
        callback();
      }, 500); // 500ms = long press padrão
    },
    onEnd: () => {
      if (this.longPressTimeout) {
        clearTimeout(this.longPressTimeout);
        this.longPressTimeout = null;
      }
    }
  });
  gesture.enable();
}
```

**Uso no {PROJETO}:** long press em mensagem → copiar texto / reagir.

---

## 6. Bottom sheet (IonModal)

```typescript
// Bottom sheet = modal com breakpoints
async openBottomSheet(): Promise<void> {
  const modal = await this.modalCtrl.create({
    component: ActionSheetComponent,
    breakpoints: [0, 0.4, 0.75],  // 0=fechado, 0.4=padrão, 0.75=expandido
    initialBreakpoint: 0.4,
    backdropBreakpoint: 0.2,       // backdrop aparece ao passar de 20%
    handle: true,                   // barra de drag visível no topo
    componentProps: { data: this.selectedItem() }
  });
  await modal.present();
}
```

```scss
// Estilizar o handle do bottom sheet
ion-modal.modal-sheet::part(handle) {
  background: var(--app-border-default);
  width: 40px;
  height: 4px;
  border-radius: 2px;
  margin: var(--sp-sm) auto;
}
```

**Quando usar bottom sheet vs modal:**
- Bottom sheet: ações rápidas, filtros, detalhes de item (< 60% da tela)
- Modal full: formulários, fluxos completos (pagamento, proposta)

---

## 7. Touch targets (acessibilidade)

```scss
// Todo elemento tappable deve ter área mínima 44×44px
ion-button {
  min-height: 44px;
  min-width: 44px;
}

// Ícones pequenos — aumentar área sem aumentar o ícone visível
.icon-tap-target {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;

  ion-icon {
    font-size: 20px; // ícone em tamanho normal
    pointer-events: none;
  }
}

// Itens de lista — padding adequado para tap confortável
ion-item {
  --min-height: 56px; // padrão Material/Ionic
}
```

---

## 8. Anti-patterns

- ❌ Nunca colocar swipe em items sem confirmação para ações destrutivas
- ❌ Nunca long press sem feedback haptic (usuário não sabe se ativou)
- ❌ Nunca touch target menor que 44×44px (WCAG 2.2, SC 2.5.8)
- ❌ Nunca bottom sheet sem handle visível (usuário não sabe que pode arrastar)
- ❌ Nunca usar gestos de sistema (swipe-back do iOS) para navegação custom — conflito
- ❌ Nunca haptic em animações que não são iniciadas pelo usuário (spam de vibração)
- ❌ Nunca swipe-to-delete sem "desfazer" disponível em toast por 3-5 segundos
