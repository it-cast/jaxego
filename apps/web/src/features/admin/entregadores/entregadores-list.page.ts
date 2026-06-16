import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '../../../shared/state';
import { AdminKycService, CourierListItem } from '../kyc/kyc.service';

/**
 * Lista de entregadores da área (F2.2 fila KYC + F2.3 lista). Filtro
 * pendentes/todos. Um entregador pendente abre a revisão de KYC; um ativo abre o
 * detalhe (score/suspensão). Sem PII além do CPF mascarado (TH-05). Tokens only.
 */
@Component({
  selector: 'jx-admin-entregadores',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [EmptyStateComponent, ErrorStateComponent, LoadingSkeletonComponent],
  template: `
    <section class="jx-couriers">
      <header class="jx-couriers__head">
        <h1 class="jx-couriers__title">Entregadores</h1>
        <div class="jx-couriers__seg" role="tablist">
          <button
            type="button"
            role="tab"
            [attr.aria-selected]="filter() === 'pending_kyc'"
            [class.jx-couriers__seg-btn--on]="filter() === 'pending_kyc'"
            class="jx-couriers__seg-btn"
            (click)="setFilter('pending_kyc')"
          >
            Fila de validação
          </button>
          <button
            type="button"
            role="tab"
            [attr.aria-selected]="filter() === 'all'"
            [class.jx-couriers__seg-btn--on]="filter() === 'all'"
            class="jx-couriers__seg-btn"
            (click)="setFilter('all')"
          >
            Todos
          </button>
        </div>
        <input
          type="search"
          class="jx-couriers__search"
          placeholder="Buscar por nome ou CPF…"
          [value]="query()"
          (input)="query.set($any($event.target).value)"
          aria-label="Buscar entregador"
        />
      </header>

      @if (loading()) {
        <jx-loading-skeleton />
      } @else if (error()) {
        <jx-error-state message="Não foi possível carregar os entregadores." (retry)="reload()" />
      } @else if (!items().length) {
        <jx-empty-state
          icon="✓"
          title="Nada na fila"
          message="Quando um entregador enviar documentos, ele aparece aqui."
        />
      } @else {
        <table class="jx-couriers__tbl">
          <thead>
            <tr>
              <th>Entregador</th>
              <th>CPF</th>
              <th>Validação</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            @for (c of filtered(); track c.id) {
              <tr class="jx-couriers__row" (click)="open(c)">
                <td>{{ c.full_name }}</td>
                <td class="jx-couriers__mono">{{ c.cpf_masked }}</td>
                <td>{{ c.kyc_level }}</td>
                <td>{{ statusLabel(c.status) }}</td>
              </tr>
            }
          </tbody>
        </table>
      }
    </section>
  `,
  styles: [
    `
      .jx-couriers {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-couriers__head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--jx-space-3);
        flex-wrap: wrap;
      }
      .jx-couriers__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0;
      }
      .jx-couriers__seg {
        display: inline-flex;
        background: var(--surface-sunken);
        border-radius: var(--jx-radius-md);
        padding: 3px;
        gap: 2px;
      }
      .jx-couriers__seg-btn {
        border: 0;
        background: transparent;
        padding: var(--jx-space-1) var(--jx-space-3);
        border-radius: var(--jx-radius-sm);
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-medium);
        color: var(--text-muted);
        cursor: pointer;
      }
      .jx-couriers__seg-btn--on {
        background: var(--surface);
        color: var(--text);
      }
      .jx-couriers__search {
        padding: var(--jx-space-2);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-md);
        background: var(--surface);
        color: var(--text);
        font-size: var(--jx-text-sm);
        min-width: 240px;
      }
      .jx-couriers__tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: var(--jx-text-sm);
      }
      .jx-couriers__tbl th {
        text-align: left;
        padding: var(--jx-space-2);
        border-bottom: 1px solid var(--border);
        font-size: var(--jx-text-xs);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
      }
      .jx-couriers__row {
        cursor: pointer;
      }
      .jx-couriers__row td {
        padding: var(--jx-space-2);
        border-bottom: 1px solid var(--surface-sunken);
      }
      .jx-couriers__row:hover td {
        background: var(--surface-elevated);
      }
      .jx-couriers__mono {
        font-family: var(--jx-font-mono);
      }
    `,
  ],
})
export class AdminEntregadoresPage implements OnInit {
  private readonly kyc = inject(AdminKycService);
  private readonly router = inject(Router);

  protected readonly items = signal<CourierListItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly filter = signal<'pending_kyc' | 'all'>('pending_kyc');
  protected readonly query = signal('');

  /** Busca client-side por nome ou CPF (a fila/lista vem filtrada por status no backend). */
  protected readonly filtered = computed<CourierListItem[]>(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return this.items();
    return this.items().filter(
      (c) =>
        c.full_name.toLowerCase().includes(q) || c.cpf_masked.toLowerCase().includes(q)
    );
  });

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    try {
      const status = this.filter() === 'pending_kyc' ? 'pending_kyc' : undefined;
      const page = await this.kyc.listCouriers(status);
      this.items.set(page.items);
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected setFilter(value: 'pending_kyc' | 'all'): void {
    this.filter.set(value);
    void this.reload();
  }

  protected open(c: CourierListItem): void {
    if (c.status === 'pending_kyc') {
      void this.router.navigate(['/admin/kyc', c.id]);
    } else {
      void this.router.navigate(['/admin/entregadores', c.id]);
    }
  }

  protected statusLabel(status: string): string {
    const map: Record<string, string> = {
      pending_kyc: 'Em análise',
      active: 'Ativo',
      suspended: 'Suspenso',
      banned: 'Banido',
    };
    return map[status] ?? status;
  }
}
