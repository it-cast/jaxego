import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { GovernancaService } from './governanca/governanca.service';

interface Queue {
  label: string;
  count: number;
  route: string;
}

/**
 * Painel do admin da área (tela tpl-a-dash). "Filas que precisam de você":
 * disputas, recursos de suspensão — contadores reais e clicáveis. KYC de
 * entregador saiu daqui (CORRECAO-255) — quem aprova/reprova é o admin do
 * time agora, não o admin da área; o link apontava pra uma rota que não
 * existe mais em /admin. Os endpoints são area-scoped pelo token (TH-09).
 * Tokens only.
 */
@Component({
  selector: 'jx-admin-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
  template: `
    <section class="jx-dash">
      <h1 class="jx-dash__title">Painel da área</h1>
      <div class="jx-dash__card">
        <h2 class="jx-dash__h2">Filas que precisam de você</h2>
        @for (q of queues(); track q.label) {
          <button type="button" class="jx-dash__queue" (click)="go(q.route)">
            <span>{{ q.label }}</span>
            <span
              class="jx-dash__count"
              [class.jx-dash__count--zero]="q.count === 0"
              >{{ q.count }}</span
            >
          </button>
        }
      </div>
    </section>
  `,
  styles: [
    `
      .jx-dash {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-dash__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0;
      }
      .jx-dash__card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
      }
      .jx-dash__h2 {
        font-size: var(--jx-text-md);
        margin: 0 0 var(--jx-space-2);
      }
      .jx-dash__queue {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--jx-space-2) 0;
        border: 0;
        border-bottom: 1px solid var(--surface-sunken);
        background: transparent;
        cursor: pointer;
        font-size: var(--jx-text-sm);
        color: var(--text);
      }
      .jx-dash__count {
        font-family: var(--jx-font-mono);
        font-weight: var(--jx-weight-bold);
        background: var(--jx-color-brand-50);
        color: var(--jx-color-brand-600);
        padding: 2px 11px;
        border-radius: var(--jx-radius-full);
      }
      .jx-dash__count--zero {
        background: var(--surface-sunken);
        color: var(--text-subtle);
      }
    `,
  ],
})
export class AdminInicioPage implements OnInit {
  private readonly governanca = inject(GovernancaService);
  private readonly router = inject(Router);

  protected readonly queues = signal<Queue[]>([
    { label: 'Disputas de pagamento direto', count: 0, route: '/admin/disputas' },
    { label: 'Recursos de suspensão', count: 0, route: '/admin/disputas' },
  ]);

  async ngOnInit(): Promise<void> {
    const [disputes, appeals] = await Promise.all([
      this.governanca.listDisputes().catch(() => []),
      this.governanca.listAppeals(true).catch(() => []),
    ]);
    this.queues.set([
      {
        label: 'Disputas de pagamento direto',
        count: disputes.length,
        route: '/admin/disputas',
      },
      {
        label: 'Recursos de suspensão',
        count: appeals.length,
        route: '/admin/disputas',
      },
    ]);
  }

  protected go(route: string): void {
    void this.router.navigate([route]);
  }
}
