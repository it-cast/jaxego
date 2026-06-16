import { ChangeDetectionStrategy, Component } from '@angular/core';
import {
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonLabel,
  IonIcon,
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  homeOutline,
  mapOutline,
  cashOutline,
  personOutline,
} from 'ionicons/icons';

/**
 * Entregador shell — mobile-first, Ionic bottom tabs (UI-SPEC §6.1).
 * Tabs: Início / Ganhos / Bairros / Perfil (fiel ao tabbar do protótipo).
 * aria-current handled by Ionic router-link-active; safe-area via Ionic defaults.
 */
@Component({
  selector: 'jx-entregador-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonTabs, IonTabBar, IonTabButton, IonLabel, IonIcon],
  template: `
    <ion-tabs>
      <ion-tab-bar slot="bottom" class="jx-tabbar">
        <ion-tab-button tab="inicio">
          <ion-icon name="home-outline" aria-hidden="true" />
          <ion-label>Início</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="saldo">
          <ion-icon name="cash-outline" aria-hidden="true" />
          <ion-label>Ganhos</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="cobertura">
          <ion-icon name="map-outline" aria-hidden="true" />
          <ion-label>Bairros</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="perfil">
          <ion-icon name="person-outline" aria-hidden="true" />
          <ion-label>Perfil</ion-label>
        </ion-tab-button>
      </ion-tab-bar>
    </ion-tabs>
  `,
  styles: [
    `
      .jx-tabbar {
        --background: var(--surface-elevated);
        --color: var(--text-muted);
        --color-selected: var(--brand);
        --border: 1px solid var(--border);
      }
    `,
  ],
})
export class EntregadorShellComponent {
  constructor() {
    addIcons({ homeOutline, mapOutline, cashOutline, personOutline });
  }
}
