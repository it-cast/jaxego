import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faHouse,
  faMap,
  faMoneyBill,
  faBoxOpen,
  faUser,
} from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'jx-entregador-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FaIconComponent],
  template: `
    <main class="jx-shell__content">
      <router-outlet />
    </main>
    <nav class="jx-shell__tabbar">
      <a routerLink="/entregador/inicio" routerLinkActive="jx-tab--active" class="jx-tab">
        <fa-icon [icon]="iconInicio" aria-hidden="true" />
        <span>Início</span>
      </a>
      <a routerLink="/entregador/saldo" routerLinkActive="jx-tab--active" class="jx-tab">
        <fa-icon [icon]="iconGanhos" aria-hidden="true" />
        <span>Ganhos</span>
      </a>
      <a routerLink="/entregador/entregas" routerLinkActive="jx-tab--active" class="jx-tab">
        <fa-icon [icon]="iconEntregas" aria-hidden="true" />
        <span>Entregas</span>
      </a>
      <a routerLink="/entregador/cobertura" routerLinkActive="jx-tab--active" class="jx-tab">
        <fa-icon [icon]="iconBairros" aria-hidden="true" />
        <span>Bairros</span>
      </a>
      <a routerLink="/entregador/perfil" routerLinkActive="jx-tab--active" class="jx-tab">
        <fa-icon [icon]="iconPerfil" aria-hidden="true" />
        <span>Perfil</span>
      </a>
    </nav>
  `,
  styles: [
    `
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
        display: flex;
        align-items: stretch;
        background: var(--surface-elevated, #fff);
        border-top: 1px solid var(--border, #e5e0d8);
        padding-bottom: env(safe-area-inset-bottom, 0);
        flex-shrink: 0;
        border-radius: 2em 2em 0 0;
        padding: .5em;
      }
      .jx-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: 6px 0 4px;
        background: none;
        border: none;
        color: var(--text-muted, #8c8279);
        font-size: 10px;
        font-weight: 600;
        text-decoration: none;
        cursor: pointer;
        transition: color 0.15s;
      }
      .jx-tab fa-icon {
        font-size: 20px;
      }
      .jx-tab--active {
        color: var(--brand, #e8722a);
      }
    `,
  ],
})
export class EntregadorShellComponent {
  protected readonly iconInicio = faHouse;
  protected readonly iconGanhos = faMoneyBill;
  protected readonly iconEntregas = faBoxOpen;
  protected readonly iconBairros = faMap;
  protected readonly iconPerfil = faUser;
}
