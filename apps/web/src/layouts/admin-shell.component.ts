import {
  ChangeDetectionStrategy,
  Component,
  signal,
} from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeToggleComponent } from '../core/theme/theme-toggle.component';

/**
 * Admin shell — desktop-first, collapsible left sidebar + dense content slot
 * (UI-SPEC §6.1).
 */
@Component({
  selector: 'jx-admin-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, ThemeToggleComponent],
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
          ☰
        </button>
        @if (!collapsed()) {
          <span class="jx-admin__brand">Jaxegô admin</span>
        }
        <div class="jx-admin__spacer"></div>
        <jx-theme-toggle />
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
      .jx-admin__spacer {
        flex: 1 1 auto;
      }
      .jx-admin__content {
        padding: var(--jx-space-5);
        background: var(--surface);
      }
    `,
  ],
})
export class AdminShellComponent {
  protected readonly collapsed = signal(false);
}
