import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faHouse,
  faMap,
  faBoxOpen,
  faUser,
} from '@fortawesome/free-solid-svg-icons';
import { OfferMonitorService } from '../features/entregador/oferta/offer-monitor.service';
import { OfferSheetComponent } from '../features/entregador/oferta/offer-sheet.component';

/**
 * Shell do entregador — layout persistente com tab bar.
 * Aqui fica o monitor global de ofertas: o poll começa quando o shell é
 * montado (entregador autenticado) e o modal aparece em cima de qualquer
 * tela, não apenas na tela de início.
 */
@Component({
  selector: 'jx-entregador-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FaIconComponent, OfferSheetComponent],
  template: `
    <main class="jx-shell__content">
      <router-outlet />
    </main>
    <nav class="jx-shell__tabbar" aria-label="Navegação do entregador">
      @for (tab of tabs; track tab.path) {
        <a
          [routerLink]="tab.path"
          routerLinkActive="jx-tab--active"
          #rla="routerLinkActive"
          [attr.aria-current]="rla.isActive ? 'page' : null"
          class="jx-tab"
        >
          <span class="jx-tab__icon"><fa-icon [icon]="tab.icon" aria-hidden="true" /></span>
          <span class="jx-tab__label">{{ tab.label }}</span>
        </a>
      }
    </nav>

    <!-- Modal global de oferta — sobrepõe qualquer tela do app -->
    <jx-offer-sheet
      class="jx-shell__offer-overlay"
      [offer]="monitor.offer()"
      [result]="monitor.offerResult()"
      [processing]="monitor.processing()"
      (accept)="monitor.accept($event)"
      (decline)="monitor.decline($event)"
    />
  `,
  styles: [
    `
      /* Redesign v3 §6.2 — tab bar flutuante (pílula elevada, blur), alvos 56px,
         indicador ativo tangerina. Tokens only (Gate 2). */
      :host {
        display: flex;
        flex-direction: column;
        height: 100vh;
        height: 100dvh;
        background-color: var(--surface);
        background-image: var(--surface-page-glow);
      }
      .jx-shell__content {
        flex: 1;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
      }
      .jx-shell__tabbar {
        flex-shrink: 0;
        display: flex;
        align-items: stretch;
        gap: var(--jx-space-1);
        margin: 0 var(--jx-space-3) calc(var(--jx-space-3) + env(safe-area-inset-bottom, 0px));
        padding: var(--jx-space-1);
        background: var(--topbar-bg);
        backdrop-filter: saturate(1.4) blur(16px);
        -webkit-backdrop-filter: saturate(1.4) blur(16px);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-2xl);
        box-shadow: var(--shadow-lg);
      }
      .jx-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        min-height: 56px;
        border-radius: var(--jx-radius-xl);
        color: var(--text-muted);
        font-size: var(--jx-text-2xs);
        font-weight: var(--jx-weight-semibold);
        letter-spacing: 0.01em;
        text-decoration: none;
        -webkit-tap-highlight-color: transparent;
        transition:
          color var(--jx-motion-fast) var(--jx-motion-easing-out),
          background var(--jx-motion-fast) var(--jx-motion-easing-out);
      }
      .jx-tab__icon {
        display: grid;
        place-items: center;
        width: 44px;
        height: 28px;
        border-radius: var(--jx-radius-full);
        font-size: var(--jx-text-lg);
        transition:
          background var(--jx-motion-normal) var(--jx-motion-spring),
          transform var(--jx-motion-normal) var(--jx-motion-spring);
      }
      .jx-tab:active .jx-tab__icon {
        transform: scale(0.9);
      }
      .jx-tab--active {
        color: var(--brand);
      }
      .jx-tab--active .jx-tab__icon {
        background: var(--brand-gradient);
        color: var(--brand-contrast);
        box-shadow: var(--shadow-glow);
      }
      .jx-tab:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
      }

      /* O jx-offer-sheet já é position:fixed — este host apenas o instancia. */
      .jx-shell__offer-overlay {
        display: contents;
      }

      @media (prefers-reduced-motion: reduce) {
        .jx-tab,
        .jx-tab__icon {
          transition: none;
        }
      }
    `,
  ],
})
export class EntregadorShellComponent implements OnInit, OnDestroy {
  protected readonly monitor = inject(OfferMonitorService);

  protected readonly tabs = [
    { path: '/entregador/inicio', label: 'Início', icon: faHouse },
    { path: '/entregador/entregas', label: 'Entregas', icon: faBoxOpen },
    { path: '/entregador/cobertura', label: 'Zonas', icon: faMap },
    { path: '/entregador/perfil', label: 'Perfil', icon: faUser },
  ];

  ngOnInit(): void {
    this.monitor.startMonitoring();
  }

  ngOnDestroy(): void {
    this.monitor.stopMonitoring();
  }
}
