import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  faGaugeHigh,
  faGear,
  faLayerGroup,
  faScaleBalanced,
  faKey,
  faStore,
  faPeopleGroup,
  faMapPin,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { AppShellComponent, type ShellNavItem } from '@jaxego/shared/layout/app-shell.component';

/**
 * Admin de área shell — wrapper do jx-app-shell (redesign v3 §6.1). Nav cobre
 * todas as telas da área + sair.
 */
@Component({
  selector: 'jx-admin-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AppShellComponent],
  template: `
    <jx-app-shell
      surfaceLabel="Admin de área"
      navAriaLabel="Navegação do admin"
      [nav]="links"
      (logout)="logout()"
    />
  `,
})
export class AdminShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly links: ShellNavItem[] = [
    { path: 'inicio', label: 'Painel', icon: faGaugeHigh },
    { path: 'equipes', label: 'Equipes', icon: faPeopleGroup },
    { path: 'config', label: 'Configurações', icon: faGear },
    { path: 'zonas', label: 'Zonas', icon: faLayerGroup },
    { path: 'bairros', label: 'Bairros', icon: faMapPin },
    { path: 'lojas', label: 'Lojas', icon: faStore },
    { path: 'disputas', label: 'Disputas', icon: faScaleBalanced },
    { path: 'api-keys', label: 'Chaves de API', icon: faKey },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/admin/entrar']);
  }
}
