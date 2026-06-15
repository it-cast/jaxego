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
  faGear,
  faMap,
  faScaleBalanced,
  faKey,
  faRightFromBracket,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons';
import { ThemeToggleComponent } from '../core/theme/theme-toggle.component';
import { AuthService } from '../core/auth/auth.service';

/**
 * Admin shell — desktop-first, collapsible left sidebar + dense content slot
 * (UI-SPEC §6.1).
 */
@Component({
  selector: 'jx-admin-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ThemeToggleComponent, FaIconComponent],
  template: `
    <div class="jx-admin" [class.jx-admin--collapsed]="collapsed()">
      <nav class="jx-admin__sidebar" aria-label="Navegação do admin">
        <button
          type="button"
          class="jx-admin__toggle"
          [attr.aria-expanded]="!collapsed()"
          aria-label="Alternar menu lateral"
          (click)="collapsed.set(!collapsed())"
        >
          <fa-icon [icon]="iconBars" />
        </button>
        @if (!collapsed()) {
          <span class="jx-admin__brand">Jaxegô admin</span>
        }
        <ul class="jx-admin__links">
          @for (link of links; track link.path) {
            <li>
              <a
                [routerLink]="link.path"
                routerLinkActive="jx-admin__link--active"
                class="jx-admin__link"
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
        <div class="jx-admin__spacer"></div>
        <jx-theme-toggle />
        <button type="button" class="jx-admin__logout" (click)="logout()">
          <fa-icon [icon]="iconLogout" [fixedWidth]="true" aria-hidden="true" />
          @if (!collapsed()) {
            <span>Sair</span>
          }
        </button>
      </nav>
      <main class="jx-admin__content">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [
    `
      .jx-admin {
        display: grid;
        grid-template-columns: 240px 1fr;
        min-height: 100vh;
      }
      .jx-admin--collapsed {
        grid-template-columns: 64px 1fr;
      }
      .jx-admin__sidebar {
        background: var(--surface-sunken);
        border-right: 1px solid var(--border);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-admin__toggle {
        min-width: 44px;
        min-height: 44px;
        background: transparent;
        border: 0;
        color: var(--text);
        font-size: var(--jx-text-lg);
        cursor: pointer;
        align-self: flex-start;
      }
      .jx-admin__brand {
        font-family: var(--jx-font-display);
        font-weight: var(--jx-weight-bold);
        color: var(--text);
      }
      .jx-admin__links {
        list-style: none;
        margin: var(--jx-space-3) 0 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-admin__link {
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
      .jx-admin__link:hover {
        background: var(--surface-elevated);
        color: var(--text);
      }
      .jx-admin__link:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
      }
      .jx-admin__link--active {
        background: var(--brand-wash);
        color: var(--brand);
      }
      .jx-admin__spacer {
        flex: 1 1 auto;
      }
      .jx-admin__content {
        padding: var(--jx-space-5);
        background: var(--surface);
      }
      .jx-admin__logout {
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
      .jx-admin__logout:hover {
        background: var(--surface-elevated);
        color: var(--error);
      }
      .jx-admin__logout:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
      }
    `,
  ],
})
export class AdminShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly collapsed = signal(false);
  protected readonly iconBars = faBars;
  protected readonly iconLogout = faRightFromBracket;

  protected readonly links: { path: string; label: string; icon: IconDefinition }[] = [
    { path: 'inicio',   label: 'Painel',        icon: faGaugeHigh },
    { path: 'config',   label: 'Configurações',  icon: faGear },
    { path: 'bairros',  label: 'Bairros',        icon: faMap },
    { path: 'disputas', label: 'Disputas',       icon: faScaleBalanced },
    { path: 'api-keys', label: 'Chaves de API',  icon: faKey },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }
}
