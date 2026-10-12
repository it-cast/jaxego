import { ChangeDetectionStrategy, Component, computed, effect, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  faGauge,
  faTruckFast,
  faStar,
  faFileInvoiceDollar,
  faCreditCard,
  faGear,
  faWallet,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { AppShellComponent, type ShellNavItem } from '@jaxego/shared/layout/app-shell.component';

/** Shell da loja — wrapper do jx-app-shell (redesign v3 §6.1). */
@Component({
  selector: 'jx-loja-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AppShellComponent],
  template: `
    <jx-app-shell
      surfaceLabel="Loja"
      navAriaLabel="Navegação da loja"
      [nav]="nav"
      [contextTitle]="tradeName()"
      [contextSubtitle]="neighborhood()"
      (logout)="logout()"
    />
  `,
})
export class LojaShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  constructor() {
    effect(() => {
      if (!this.auth.isAuthenticated()) {
        void this.router.navigate(['/entrar']);
      }
    });
  }

  protected readonly tradeName = computed(() => this.auth.me()?.trade_name ?? '');
  protected readonly neighborhood = computed(() => this.auth.me()?.address_neighborhood ?? '');

  protected readonly nav: ShellNavItem[] = [
    { path: '/loja/painel', label: 'Painel', icon: faGauge },
    { path: '/loja/entregas', label: 'Entregas', icon: faTruckFast },
    { path: '/loja/favoritos', label: 'Favoritos/Bloqueados', icon: faStar },
    { path: '/loja/faturas', label: 'Faturas', icon: faFileInvoiceDollar },
    { path: '/loja/saldo', label: 'Meu saldo', icon: faWallet },
    { path: '/loja/plano', label: 'Plano', icon: faCreditCard },
    { path: '/loja/config', label: 'Configurações', icon: faGear },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }
}
