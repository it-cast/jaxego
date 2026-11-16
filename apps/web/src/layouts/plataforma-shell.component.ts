import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  faGaugeHigh,
  faUsers,
  faMap,
  faScaleBalanced,
  faCreditCard,
  faUserShield,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { AppShellComponent, type ShellNavItem } from '@jaxego/shared/layout/app-shell.component';

/**
 * Platform-admin shell (UI-SPEC telas 23-25 / D-06) — wrapper do jx-app-shell
 * (redesign v3 §6.1). Rotas cross-área (acesso auditado, TOTP — backend).
 */
@Component({
  selector: 'jx-plataforma-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AppShellComponent],
  template: `
    <jx-app-shell
      surfaceLabel="Plataforma"
      navAriaLabel="Navegação da plataforma"
      [nav]="links"
      (logout)="logout()"
    />
  `,
})
export class PlataformaShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly links: ShellNavItem[] = [
    { path: 'visao-geral', label: 'Visão geral', icon: faGaugeHigh },
    { path: 'areas', label: 'Áreas', icon: faMap },
    { path: 'pessoas', label: 'Entregadores e lojas', icon: faUsers },
    { path: 'planos', label: 'Planos', icon: faCreditCard },
    { path: 'admins', label: 'Admins de área', icon: faUserShield },
    { path: 'disputas', label: 'Disputas e suspensões', icon: faScaleBalanced },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/plataforma/entrar']);
  }
}
