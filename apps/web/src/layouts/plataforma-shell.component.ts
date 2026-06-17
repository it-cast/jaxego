import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faBars,
  faGaugeHigh,
  faUsers,
  faMap,
  faScaleBalanced,
  faRightFromBracket,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons';
import { ThemeToggleComponent } from '@jaxego/core/theme/theme-toggle.component';
import { AuthService } from '@jaxego/core/auth/auth.service';

/**
 * Platform-admin shell (UI-SPEC telas 23-25 / D-06) — desktop-first, collapsible
 * left sidebar + dense content slot. Mirrors the area admin shell, but its routes
 * are the cross-area platform surface (acesso auditado, TOTP — backend). Tokens
 * only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-plataforma-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    ThemeToggleComponent,
    FaIconComponent,
  ],
  template: `
    <div class="jx-plat" [class.jx-plat--collapsed]="collapsed()">
      <nav class="jx-plat__sidebar" aria-label="Navegação da plataforma">
        <button
          type="button"
          class="jx-plat__toggle"
          [attr.aria-expanded]="!collapsed()"
          aria-label="Alternar menu lateral"
          (click)="collapsed.set(!collapsed())"
        >
          <fa-icon [icon]="iconBars" />
        </button>
        @if (!collapsed()) {
          <span class="jx-plat__brand">Jaxegô plataforma</span>
        }
        <ul class="jx-plat__links">
          @for (link of links; track link.path) {
            <li>
              <a
                [routerLink]="link.path"
                routerLinkActive="jx-plat__link--active"
                class="jx-plat__link"
                [attr.aria-label]="link.label"
              >
                <fa-icon [icon]="link.icon" [fixedWidth]="true" aria-hidden="true" />
                @if (!collapsed()) {
                  <span>{{ link.label }}</span>
                }
              </a>
            </li>
          }
        </ul>
        <div class="jx-plat__spacer"></div>
        <jx-theme-toggle />
        <button type="button" class="jx-plat__logout" (click)="logout()">
          <fa-icon [icon]="iconLogout" [fixedWidth]="true" aria-hidden="true" />
          @if (!collapsed()) {
            <span>Sair</span>
          }
        </button>
      </nav>
      <main class="jx-plat__content">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [
    `
      .jx-plat {
        display: grid;
        grid-template-columns: 240px 1fr;
        min-height: 100vh;
      }
      .jx-plat--collapsed {
        grid-template-columns: 64px 1fr;
      }
      .jx-plat__sidebar {
        background: var(--surface-sunken);
        border-right: 1px solid var(--border);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-plat__toggle {
        min-width: 44px;
        min-height: 44px;
        background: transparent;
        border: 0;
        color: var(--text);
        font-size: var(--jx-text-lg);
        cursor: pointer;
        align-self: flex-start;
      }
      .jx-plat__brand {
        font-family: var(--jx-font-display);
        font-weight: var(--jx-weight-bold);
        color: var(--text);
      }
      .jx-plat__links {
        list-style: none;
        margin: var(--jx-space-3) 0 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-plat__link {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
        min-height: 44px;
        padding: 0 var(--jx-space-2);
        border-radius: var(--jx-radius-lg);
        color: var(--text-muted);
        text-decoration: none;
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-semibold);
      }
      .jx-plat__link:hover {
        background: var(--surface-elevated);
        color: var(--text);
      }
      .jx-plat__link:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
      }
      .jx-plat__link--active {
        background: var(--brand-wash);
        color: var(--brand);
      }
      .jx-plat__spacer {
        flex: 1 1 auto;
      }
      .jx-plat__content {
        padding: var(--jx-space-5);
        background: var(--surface);
      }
      .jx-plat__logout {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
        min-height: 44px;
        width: 100%;
        padding: 0 var(--jx-space-2);
        border: 0;
        border-radius: var(--jx-radius-lg);
        background: transparent;
        color: var(--text-muted);
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-semibold);
        cursor: pointer;
        text-align: left;
      }
      .jx-plat__logout:hover {
        background: var(--surface-elevated);
        color: var(--error);
      }
      .jx-plat__logout:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
      }
    `,
  ],
})
export class PlataformaShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly collapsed = signal(false);
  protected readonly iconBars = faBars;
  protected readonly iconLogout = faRightFromBracket;

  protected readonly links: { path: string; label: string; icon: IconDefinition }[] = [
    { path: 'visao-geral', label: 'Visão geral', icon: faGaugeHigh },
    { path: 'areas', label: 'Áreas', icon: faMap },
    { path: 'pessoas', label: 'Entregadores e lojas', icon: faUsers },
    { path: 'disputas', label: 'Disputas e suspensões', icon: faScaleBalanced },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }
}
