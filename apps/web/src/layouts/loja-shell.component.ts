import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faRightFromBracket } from '@fortawesome/free-solid-svg-icons';
import { ThemeToggleComponent } from '../core/theme/theme-toggle.component';
import { AuthService } from '../core/auth/auth.service';

/**
 * Loja shell — web responsive, centered 620–860px, simple topbar + content slot
 * (UI-SPEC §6.1).
 */
@Component({
  selector: 'jx-loja-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, ThemeToggleComponent, FaIconComponent],
  template: `
    <header class="jx-loja-topbar">
      <nav class="jx-loja-topbar__inner" aria-label="Navegação da loja">
        <span class="jx-loja-topbar__brand">Jaxegô</span>
        <div class="jx-loja-topbar__actions">
          <jx-theme-toggle />
          <button type="button" class="jx-loja-topbar__logout" (click)="logout()">
            <fa-icon [icon]="iconLogout" aria-hidden="true" />
            <span>Sair</span>
          </button>
        </div>
      </nav>
    </header>
    <main class="jx-loja-main">
      <router-outlet />
    </main>
  `,
  styles: [
    `
      .jx-loja-topbar {
        background: var(--surface-elevated);
        border-bottom: 1px solid var(--border);
      }
      .jx-loja-topbar__inner {
        max-width: 860px;
        margin: 0 auto;
        padding: var(--jx-space-3) var(--jx-space-4);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .jx-loja-topbar__brand {
        font-family: var(--jx-font-display);
        font-weight: var(--jx-weight-bold);
        font-size: var(--jx-text-lg);
        color: var(--text);
      }
      .jx-loja-main {
        max-width: 860px;
        margin: 0 auto;
        padding: var(--jx-space-5) var(--jx-space-4);
      }
      .jx-loja-topbar__actions {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
      }
      .jx-loja-topbar__logout {
        display: flex;
        align-items: center;
        gap: var(--jx-space-1);
        min-height: 44px;
        padding: 0 var(--jx-space-2);
        border: 0;
        border-radius: var(--jx-radius-lg);
        background: transparent;
        color: var(--text-muted);
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-semibold);
        cursor: pointer;
      }
      .jx-loja-topbar__logout:hover {
        background: var(--surface-sunken);
        color: var(--error);
      }
      .jx-loja-topbar__logout:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
      }
    `,
  ],
})
export class LojaShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  protected readonly iconLogout = faRightFromBracket;

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }
}
