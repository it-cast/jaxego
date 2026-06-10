import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeToggleComponent } from '../core/theme/theme-toggle.component';

/**
 * Loja shell — web responsive, centered 620–860px, simple topbar + content slot
 * (UI-SPEC §6.1).
 */
@Component({
  selector: 'jx-loja-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, ThemeToggleComponent],
  template: `
    <header class="jx-loja-topbar">
      <nav class="jx-loja-topbar__inner" aria-label="Navegação da loja">
        <span class="jx-loja-topbar__brand">Jaxegô</span>
        <jx-theme-toggle />
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
    `,
  ],
})
export class LojaShellComponent {}
