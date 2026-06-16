import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ThemeToggleComponent } from '../core/theme/theme-toggle.component';

/**
 * Loja shell — web responsive, centered 620–860px, topbar com navegação + slot
 * de conteúdo (UI-SPEC §6.1). Nav fiel ao protótipo: Painel / Entregas / Plano.
 */
@Component({
  selector: 'jx-loja-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ThemeToggleComponent],
  template: `
    <header class="jx-loja-topbar">
      <nav class="jx-loja-topbar__inner" aria-label="Navegação da loja">
        <span class="jx-loja-topbar__brand">Jaxegô</span>
        <div class="jx-loja-topbar__links">
          @for (item of nav; track item.path) {
            <a
              [routerLink]="item.path"
              routerLinkActive="jx-loja-topbar__link--on"
              class="jx-loja-topbar__link"
            >
              {{ item.label }}
            </a>
          }
        </div>
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
      .jx-loja-topbar__links {
        display: flex;
        gap: var(--jx-space-3);
        flex: 1;
        margin-left: var(--jx-space-4);
      }
      .jx-loja-topbar__link {
        color: var(--text-muted);
        text-decoration: none;
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-medium);
      }
      .jx-loja-topbar__link:hover {
        color: var(--text);
      }
      .jx-loja-topbar__link--on {
        color: var(--brand);
        font-weight: var(--jx-weight-bold);
      }
      .jx-loja-main {
        max-width: 860px;
        margin: 0 auto;
        padding: var(--jx-space-5) var(--jx-space-4);
      }
    `,
  ],
})
export class LojaShellComponent {
  protected readonly nav = [
    { path: '/loja/painel', label: 'Painel' },
    { path: '/loja/entregas', label: 'Entregas' },
    { path: '/loja/favoritos', label: 'Favoritos' },
    { path: '/loja/faturas', label: 'Faturas' },
    { path: '/loja/plano', label: 'Plano' },
  ];
}
