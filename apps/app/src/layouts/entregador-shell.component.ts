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
      /* Menu de baixo como antes do redesign v3 (pedido do Roger, 17/11/2026): barra branca reta de ponta a ponta,
         presa no rodapé, sem curva (a curva deixava o cinza da página aparecer nos cantos); o ativo muda só a cor. Sem pílula flutuante (a margem
         deixava uma faixa cinza e a altura maior escondia o fim das telas). */
      :host {
        display: flex;
        flex-direction: column;
        height: 100vh;
        height: 100dvh;
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
        background: var(--surface-elevated, #fff);
        border-top: 1px solid var(--border, #e5e0d8);
        padding: 0.5em 0.5em calc(0.5em + env(safe-area-inset-bottom, 0px));
      }
      .jx-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: 6px 0 4px;
        color: var(--text-muted, #8c8279);
        font-size: 10px;
        font-weight: 600;
        text-decoration: none;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
        transition: color 0.15s;
      }
      .jx-tab__icon {
        font-size: 20px;
        line-height: 1;
      }
      .jx-tab--active {
        color: var(--brand, #e8722a);
      }
      .jx-tab:focus-visible {
        outline: none;
        box-shadow: var(--focus-ring);
        border-radius: var(--jx-radius-xl);
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
