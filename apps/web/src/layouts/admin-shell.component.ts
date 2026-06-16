import {
  ChangeDetectionStrategy,
  Component,
  signal,
} from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ThemeToggleComponent } from '../core/theme/theme-toggle.component';

/**
 * Admin shell — desktop-first, collapsible left sidebar + dense content slot
 * (UI-SPEC §6.1).
 */
@Component({
  selector: 'jx-admin-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ThemeToggleComponent],
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
        <ul class="jx-admin__nav">
          @for (item of nav; track item.path) {
            <li>
              <a
                [routerLink]="item.path"
                routerLinkActive="jx-admin__link--on"
                class="jx-admin__link"
                [title]="item.label"
              >
                <span class="jx-admin__ic" aria-hidden="true">{{ item.icon }}</span>
                @if (!collapsed()) {
                  <span>{{ item.label }}</span>
                }
              </a>
            </li>
          }
        </ul>
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
      .jx-admin__nav {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-admin__link {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
        padding: var(--jx-space-2);
        border-radius: var(--jx-radius-md);
        color: var(--text-muted);
        text-decoration: none;
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-medium);
      }
      .jx-admin__link:hover {
        background: var(--surface-elevated);
        color: var(--text);
      }
      .jx-admin__link--on {
        background: var(--surface-elevated);
        color: var(--brand);
        font-weight: var(--jx-weight-bold);
      }
      .jx-admin__ic {
        width: 18px;
        text-align: center;
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

  protected readonly nav = [
    { path: '/admin/inicio', label: 'Painel', icon: '▦' },
    { path: '/admin/entregadores', label: 'Entregadores', icon: '✓' },
    { path: '/admin/config', label: 'Configurações', icon: '⚙' },
    { path: '/admin/bairros', label: 'Bairros', icon: '◰' },
    { path: '/admin/disputas', label: 'Disputas', icon: '⚖' },
    { path: '/admin/api-keys', label: 'API keys', icon: '⚿' },
  ];
}
