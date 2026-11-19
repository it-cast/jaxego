import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faBoxOpen, faCircleCheck, faMotorcycle, faXmark } from '@fortawesome/free-solid-svg-icons';
import { AvisosEntregaService } from './avisos-entrega.service';

/** Avisos de mudança das entregas (canto da tela). Clicar abre a entrega. */
@Component({
  selector: 'jx-avisos-entrega',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FaIconComponent],
  template: `
    <div class="jx-avisos" role="status" aria-live="polite">
      @for (a of svc.avisos(); track a.id) {
        <div class="jx-aviso" [attr.data-estado]="a.estado">
          <button type="button" class="jx-aviso__corpo" (click)="abrir(a.deliveryId, a.id)">
            <span class="jx-aviso__icone" aria-hidden="true"><fa-icon [icon]="icone(a.estado)" /></span>
            <span class="jx-aviso__texto">{{ a.texto }}</span>
            <span class="jx-aviso__ver">Ver entrega</span>
          </button>
          <button type="button" class="jx-aviso__fechar" aria-label="Fechar aviso" (click)="svc.fechar(a.id)">
            <fa-icon [icon]="i.fechar" aria-hidden="true" />
          </button>
        </div>
      }
    </div>
  `,
  styles: `
    .jx-avisos {
      position: fixed;
      right: var(--jx-space-4);
      bottom: var(--jx-space-4);
      z-index: 1500;
      display: flex;
      flex-direction: column;
      gap: var(--jx-space-2);
      width: min(380px, calc(100vw - 2 * var(--jx-space-4)));
      pointer-events: none;
    }
    .jx-aviso {
      display: flex;
      align-items: stretch;
      background: var(--surface-elevated);
      border: 1px solid var(--border);
      border-left: 4px solid var(--brand);
      border-radius: var(--jx-radius-lg);
      box-shadow: var(--shadow-lg);
      pointer-events: auto;
      animation: jx-aviso-in var(--jx-motion-slow, 240ms) var(--jx-motion-easing-out, ease-out) backwards;
    }
    .jx-aviso[data-estado='ENTREGUE'] {
      border-left-color: var(--success);
    }
    .jx-aviso__corpo {
      flex: 1;
      display: grid;
      grid-template-columns: auto 1fr;
      column-gap: var(--jx-space-3);
      row-gap: 2px;
      align-items: center;
      padding: var(--jx-space-3);
      background: none;
      border: 0;
      color: var(--text);
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .jx-aviso__icone {
      grid-row: span 2;
      display: grid;
      place-items: center;
      width: 36px;
      height: 36px;
      border-radius: var(--jx-radius-full);
      background: var(--brand-wash);
      color: var(--brand);
    }
    .jx-aviso[data-estado='ENTREGUE'] .jx-aviso__icone {
      background: var(--success-wash, var(--brand-wash));
      color: var(--success);
    }
    .jx-aviso__texto {
      font-size: var(--jx-text-sm);
      font-weight: var(--jx-weight-semibold);
      line-height: 1.35;
    }
    .jx-aviso__ver {
      font-size: var(--jx-text-xs);
      font-weight: var(--jx-weight-bold);
      color: var(--brand);
    }
    .jx-aviso__fechar {
      min-width: 44px;
      background: none;
      border: 0;
      border-left: 1px solid var(--border);
      color: var(--text-muted);
      cursor: pointer;
    }
    .jx-aviso__fechar:hover {
      color: var(--text);
      background: var(--surface-hover);
    }
    .jx-aviso__corpo:focus-visible,
    .jx-aviso__fechar:focus-visible {
      outline: none;
      box-shadow: var(--focus-ring);
    }
    @keyframes jx-aviso-in {
      from {
        opacity: 0;
        transform: translateY(12px);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .jx-aviso {
        animation: none;
      }
    }
  `,
})
export class AvisosEntregaComponent {
  protected readonly svc = inject(AvisosEntregaService);
  private readonly router = inject(Router);
  protected readonly i = { fechar: faXmark };

  protected icone(estado: string) {
    if (estado === 'ENTREGUE') return faCircleCheck;
    if (estado === 'COLETADA') return faBoxOpen;
    return faMotorcycle;
  }

  protected abrir(deliveryId: number, avisoId: number): void {
    this.svc.fechar(avisoId);
    void this.router.navigate(['/loja/entregas', deliveryId]);
  }
}
