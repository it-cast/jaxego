import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faBars,
  faGaugeHigh,
  faUsers,
  faBoxOpen,
  faLayerGroup,
  faRightFromBracket,
  faXmark,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';

@Component({
  selector: 'jx-equipe-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FaIconComponent],
  template: `
    <header class="jx-mobile-bar">
      <span class="jx-mobile-bar__brand">Jaxegô · Equipe</span>
      <button class="jx-mobile-bar__toggle" (click)="menuOpen.set(true)">
        <fa-icon [icon]="iconBars" aria-hidden="true" />
      </button>
    </header>

    @if (menuOpen()) {
      <div class="jx-sidebar-overlay" (click)="menuOpen.set(false)"></div>
    }

    <aside class="jx-sidebar" [class.jx-sidebar--open]="menuOpen()">
      <div class="jx-sidebar__header">
        <span class="jx-sidebar__brand">Jaxegô</span>
        <button class="jx-sidebar__close" (click)="menuOpen.set(false)">
          <fa-icon [icon]="iconClose" aria-hidden="true" />
        </button>
      </div>

      <nav class="jx-sidebar__nav" aria-label="Navegação da equipe">
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

    <main class="jx-equipe-main">
      <router-outlet />
    </main>
  `,
  styles: [`
    :host { display: flex; min-height: 100vh; }

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
    @media (min-width: 860px) { .jx-sidebar { transform: translateX(0); } }

    .jx-sidebar__header { display: flex; align-items: center; justify-content: space-between; padding: var(--jx-space-4); border-bottom: 1px solid var(--border, #e5e5e5); }
    .jx-sidebar__brand { font-family: var(--jx-font-display); font-weight: 800; font-size: 22px; color: var(--brand, #e8722a); }
    .jx-sidebar__close { width: 36px; height: 36px; border: 0; background: transparent; color: var(--text-muted); font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    @media (min-width: 860px) { .jx-sidebar__close { display: none; } }

    .jx-sidebar__nav { flex: 1; display: flex; flex-direction: column; padding: var(--jx-space-3) var(--jx-space-2); gap: 2px; overflow-y: auto; }
    .jx-sidebar__link { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 8px; font-size: 14px; font-weight: 500; color: var(--text-muted, #666); text-decoration: none; }
    .jx-sidebar__link:hover { background: var(--bg-hover, #f5f5f5); color: var(--text); }
    .jx-sidebar__link--on { background: var(--brand-wash, hsl(24 80% 95%)); color: var(--brand, #e8722a); font-weight: 700; }
    .jx-sidebar__link-icon { width: 20px; text-align: center; font-size: 16px; }

    .jx-sidebar__footer { padding: var(--jx-space-3) var(--jx-space-4); border-top: 1px solid var(--border, #eee); }
    .jx-sidebar__logout { display: flex; align-items: center; gap: 8px; width: 100%; padding: 10px 14px; border: 0; border-radius: 8px; background: transparent; color: var(--error, #d32f2f); font-size: 14px; font-weight: 600; cursor: pointer; }
    .jx-sidebar__logout:hover { background: var(--error-wash, hsl(0 70% 95%)); }

    .jx-sidebar-overlay { position: fixed; inset: 0; z-index: 99; background: rgba(0,0,0,0.4); }
    @media (min-width: 860px) { .jx-sidebar-overlay { display: none; } }

    .jx-mobile-bar { position: fixed; top: 0; left: 0; right: 0; z-index: 50; display: flex; align-items: center; justify-content: space-between; padding: 0 var(--jx-space-4); height: 56px; background: var(--surface-elevated, #fff); border-bottom: 1px solid var(--border, #e5e5e5); }
    .jx-mobile-bar__brand { font-family: var(--jx-font-display); font-weight: 800; font-size: 20px; color: var(--brand, #e8722a); }
    .jx-mobile-bar__toggle { width: 44px; height: 44px; border: 0; background: transparent; color: var(--text); font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    @media (min-width: 860px) { .jx-mobile-bar { display: none; } }

    .jx-equipe-main { flex: 1; padding: 3em; padding-top: calc(56px + 3em); }
    @media (min-width: 860px) { .jx-equipe-main { margin-left: 260px; padding-top: 3em; } }
  `],
})
export class EquipeShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly iconBars = faBars;
  protected readonly iconClose = faXmark;
  protected readonly iconLogout = faRightFromBracket;
  protected readonly menuOpen = signal(false);

  protected readonly nav: { path: string; label: string; icon: IconDefinition }[] = [
    { path: 'painel', label: 'Painel', icon: faGaugeHigh },
    { path: 'entregadores', label: 'Entregadores', icon: faUsers },
    { path: 'entregas', label: 'Entregas', icon: faBoxOpen },
    { path: 'zonas', label: 'Zonas', icon: faLayerGroup },
  ];

  protected async logout(): Promise<void> {
    await this.auth.logout();
    void this.router.navigate(['/equipe/entrar']);
  }
}
