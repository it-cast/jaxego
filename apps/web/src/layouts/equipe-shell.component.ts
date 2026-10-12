import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  faGaugeHigh,
  faUsers,
  faBoxOpen,
  faLayerGroup,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { AppShellComponent, type ShellNavItem } from '@jaxego/shared/layout/app-shell.component';

/** Shell da equipe — wrapper do jx-app-shell (redesign v3 §6.1). */
@Component({
  selector: 'jx-equipe-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AppShellComponent],
  template: `
    <jx-app-shell
      surfaceLabel="Equipe"
      navAriaLabel="Navegação da equipe"
      [nav]="nav"
      (logout)="logout()"
    />
  `,
})
export class EquipeShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly nav: ShellNavItem[] = [
    { path: 'painel', label: 'Painel', icon: faGaugeHigh },
    { path: 'entregadores', label: 'Entregadores', icon: faUsers },
    { path: 'entregas', label: 'Entregas', icon: faBoxOpen },
    { path: 'zonas', label: 'Zonas', icon: faLayerGroup },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/equipe/entrar']);
  }
}
