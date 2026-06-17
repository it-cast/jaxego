import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonLabel,
} from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faHouse,
  faMap,
  faMoneyBill,
  faUser,
  faRightFromBracket,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';

/**
 * Entregador shell — mobile-first, Ionic bottom tabs (UI-SPEC §6.1).
 * Tabs fiéis ao protótipo: Início / Ganhos / Bairros / Perfil (+ Sair).
 */
@Component({
  selector: 'jx-entregador-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonTabs, IonTabBar, IonTabButton, IonLabel, FaIconComponent],
  template: `
    <ion-tabs>
      <ion-tab-bar slot="bottom" class="jx-tabbar">
        <ion-tab-button tab="inicio">
          <fa-icon [icon]="iconInicio" aria-hidden="true" />
          <ion-label>Início</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="saldo">
          <fa-icon [icon]="iconGanhos" aria-hidden="true" />
          <ion-label>Ganhos</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="cobertura">
          <fa-icon [icon]="iconBairros" aria-hidden="true" />
          <ion-label>Bairros</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="perfil">
          <fa-icon [icon]="iconPerfil" aria-hidden="true" />
          <ion-label>Perfil</ion-label>
        </ion-tab-button>
        <ion-tab-button (click)="logout()">
          <fa-icon [icon]="iconLogout" aria-hidden="true" />
          <ion-label>Sair</ion-label>
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
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly iconInicio = faHouse;
  protected readonly iconGanhos = faMoneyBill;
  protected readonly iconBairros = faMap;
  protected readonly iconPerfil = faUser;
  protected readonly iconLogout = faRightFromBracket;

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }
}
