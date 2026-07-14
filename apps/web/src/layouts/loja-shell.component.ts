import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import {
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faRightFromBracket,
  faGauge,
  faTruckFast,
  faStar,
  faFileInvoiceDollar,
  faCreditCard,
  faGear,
  faBars,
  faXmark,
  faWallet,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';

@Component({
  selector: 'jx-loja-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    FaIconComponent,
  ],
  template: `
    <!-- Mobile topbar -->
    <header class="jx-mobile-bar">
      <span class="jx-mobile-bar__brand">Jaxegô</span>
      <button class="jx-mobile-bar__toggle" (click)="menuOpen.set(true)">
        <fa-icon [icon]="iconBars" aria-hidden="true" />
      </button>
    </header>

    <!-- Overlay -->
    @if (menuOpen()) {
      <div class="jx-sidebar-overlay" (click)="menuOpen.set(false)"></div>
    }

    <!-- Sidebar -->
    <aside class="jx-sidebar" [class.jx-sidebar--open]="menuOpen()">
      <div class="jx-sidebar__header">
        <span class="jx-sidebar__brand">Jaxegô</span>
        <button class="jx-sidebar__close" (click)="menuOpen.set(false)">
          <fa-icon [icon]="iconClose" aria-hidden="true" />
        </button>
      </div>

      @if (tradeName()) {
        <div class="jx-sidebar__store">
          <span class="jx-sidebar__store-name">{{ tradeName() }}</span>
        </div>
      }

      <nav class="jx-sidebar__nav" aria-label="Navegação da loja">
        @for (item of nav; track item.path) {
          <a
            [routerLink]="item.path"
            routerLinkActive="jx-sidebar__link--on"
            class="jx-sidebar__link"
            (click)="menuOpen.set(false)"
          >
            <fa-icon [icon]="item.icon" class="jx-sidebar__link-icon" aria-hidden="true" />
            {{ item.label }}
          </a>
        }
      </nav>

      <div class="jx-sidebar__footer">
        <button type="button" class="jx-sidebar__logout" (click)="logout()">
          <fa-icon [icon]="iconLogout" aria-hidden="true" />
          Sair da conta
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="jx-loja-main" [class.jx-loja-main--shifted]="true">
      <router-outlet />
    </main>
  `,
  styles: [`
    :host { display: flex; min-height: 100vh; }

    /* Sidebar */
    .jx-sidebar {
      position: fixed; top: 0; left: 0; bottom: 0;
      width: 260px; z-index: 100;
      background: var(--surface-elevated, #fff);
      border-right: 1px solid var(--border, #e5e5e5);
      display: flex; flex-direction: column;
      transform: translateX(-100%);
      transition: transform .25s ease;
    }
    .jx-sidebar--open { transform: translateX(0); }
    @media (min-width: 860px) {
      .jx-sidebar { transform: translateX(0); }
    }

    .jx-sidebar__header {
      display: flex; align-items: center; justify-content: space-between;
      padding: var(--jx-space-4);
      border-bottom: 1px solid var(--border, #e5e5e5);
    }
    .jx-sidebar__brand {
      font-family: var(--jx-font-display);
      font-weight: 800; font-size: 22px;
      color: var(--brand, #e8722a);
    }
    .jx-sidebar__close {
      width: 36px; height: 36px; border: 0; background: transparent;
      color: var(--text-muted, #888); font-size: 18px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    @media (min-width: 860px) {
      .jx-sidebar__close { display: none; }
    }

    .jx-sidebar__store {
      padding: var(--jx-space-3) var(--jx-space-4);
      border-bottom: 1px solid var(--border, #eee);
    }
    .jx-sidebar__store-name {
      font-size: 14px; font-weight: 600; color: var(--text);
    }

    .jx-sidebar__nav {
      flex: 1; display: flex; flex-direction: column;
      padding: var(--jx-space-3) var(--jx-space-2);
      gap: 2px; overflow-y: auto;
    }

    .jx-sidebar__link {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 14px;
      border-radius: var(--jx-radius-md, 8px);
      font-size: 14px; font-weight: 500;
      color: var(--text-muted, #666);
      text-decoration: none;
      transition: background .15s, color .15s;
    }
    .jx-sidebar__link:hover { background: var(--bg-hover, #f5f5f5); color: var(--text); }
    .jx-sidebar__link--on {
      background: var(--brand-wash, hsl(24 80% 95%));
      color: var(--brand, #e8722a);
      font-weight: 700;
    }
    .jx-sidebar__link-icon { width: 20px; text-align: center; font-size: 16px; }

    .jx-sidebar__footer {
      padding: var(--jx-space-3) var(--jx-space-4);
      border-top: 1px solid var(--border, #eee);
    }
    .jx-sidebar__logout {
      display: flex; align-items: center; gap: 8px;
      width: 100%; padding: 10px 14px;
      border: 0; border-radius: var(--jx-radius-md, 8px);
      background: transparent;
      color: var(--error, #d32f2f);
      font-size: 14px; font-weight: 600; cursor: pointer;
    }
    .jx-sidebar__logout:hover { background: var(--error-wash, hsl(0 70% 95%)); }

    /* Overlay */
    .jx-sidebar-overlay {
      position: fixed; inset: 0; z-index: 99;
      background: rgba(0,0,0,0.4);
      animation: fadeIn .2s ease;
    }
    @media (min-width: 860px) {
      .jx-sidebar-overlay { display: none; }
    }

    /* Mobile topbar */
    .jx-mobile-bar {
      position: fixed; top: 0; left: 0; right: 0; z-index: 50;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 var(--jx-space-4);
      height: 56px;
      background: var(--surface-elevated, #fff);
      border-bottom: 1px solid var(--border, #e5e5e5);
    }
    .jx-mobile-bar__brand {
      font-family: var(--jx-font-display);
      font-weight: 800; font-size: 20px;
      color: var(--brand, #e8722a);
    }
    .jx-mobile-bar__toggle {
      width: 44px; height: 44px; border: 0; background: transparent;
      color: var(--text); font-size: 20px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    @media (min-width: 860px) {
      .jx-mobile-bar { display: none; }
    }

    /* Main content */
    .jx-loja-main {
      flex: 1;
      padding: 3em;
      padding-top: calc(56px + 3em);
    }
    @media (min-width: 860px) {
      .jx-loja-main {
        margin-left: 260px;
        padding-top: 3em;
      }
    }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `],
})
export class LojaShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  constructor() {
    effect(() => {
      if (!this.auth.isAuthenticated()) {
        void this.router.navigate(['/entrar']);
      }
    });
  }

  protected readonly iconLogout = faRightFromBracket;
  protected readonly iconBars = faBars;
  protected readonly iconClose = faXmark;

  protected readonly menuOpen = signal(false);

  protected readonly tradeName = () => this.auth.me()?.trade_name ?? '';

  protected readonly nav = [
    { path: '/loja/painel', label: 'Painel', icon: faGauge },
    { path: '/loja/entregas', label: 'Entregas', icon: faTruckFast },
    { path: '/loja/favoritos', label: 'Favoritos/Bloqueados', icon: faStar },
    { path: '/loja/faturas', label: 'Faturas', icon: faFileInvoiceDollar },
    { path: '/loja/saldo', label: 'Meu saldo', icon: faWallet },
    { path: '/loja/plano', label: 'Plano', icon: faCreditCard },
    { path: '/loja/config', label: 'Configurações', icon: faGear },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }
}
