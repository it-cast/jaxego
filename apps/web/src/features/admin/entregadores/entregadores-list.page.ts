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
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '../../../shared/components/data-table/data-table.component';
import { AdminKycService, CourierListItem } from '../kyc/kyc.service';

interface CourierRow extends CourierListItem {
  status_label: string;
}

type SortDir = 'asc' | 'desc' | 'none';
const PAGE_SIZE = 10;

/**
 * Lista de entregadores da área (F2.2 fila KYC + F2.3 lista) com profundidade
 * operacional (MG-2.3): busca + filtro de status + jx-data-table (ordenação por
 * coluna, estados loading/empty/error) + paginação. Tokens only.
 */
@Component({
  selector: 'jx-admin-entregadores',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent],
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
          (input)="onSearch($event)"
          aria-label="Buscar entregador"
        />
      </header>

      <jx-data-table
        [columns]="columns"
        [rows]="paged()"
        [state]="tableState()"
        [hasActions]="true"
        [trackBy]="trackById"
        caption="Entregadores da área"
        emptyIcon="✓"
        emptyTitle="Nada na fila"
        emptyMessage="Quando um entregador enviar documentos, ele aparece aqui."
        errorMessage="Não foi possível carregar os entregadores."
        (sortChange)="onSort($event)"
        (retry)="reload()"
      >
        <ng-template #row let-c>
          <td>{{ c.full_name }}</td>
          <td class="jx-couriers__mono">{{ c.cpf_masked }}</td>
          <td>{{ c.kyc_level }}</td>
          <td>{{ c.status_label }}</td>
          <td>
            <button type="button" class="jx-couriers__open" (click)="open(c)">
              {{ c.status === 'pending_kyc' ? 'Revisar' : 'Abrir' }}
            </button>
          </td>
        </ng-template>
      </jx-data-table>

      @if (totalPages() > 1) {
        <nav class="jx-couriers__pager" aria-label="Paginação">
          <button type="button" (click)="prevPage()" [disabled]="page() === 0">
            ← Anterior
          </button>
          <span class="jx-couriers__pageinfo">
            Página {{ page() + 1 }} de {{ totalPages() }}
          </span>
          <button
            type="button"
            (click)="nextPage()"
            [disabled]="page() >= totalPages() - 1"
          >
            Próxima →
          </button>
        </nav>
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
      .jx-couriers__mono {
        font-family: var(--jx-font-mono);
      }
      .jx-couriers__open {
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--brand);
        border-radius: var(--jx-radius-sm);
        padding: 4px 12px;
        font-weight: var(--jx-weight-semibold);
        cursor: pointer;
      }
      .jx-couriers__pager {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--jx-space-3);
        font-size: var(--jx-text-sm);
      }
      .jx-couriers__pager button {
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        border-radius: var(--jx-radius-sm);
        padding: 6px 12px;
        cursor: pointer;
      }
      .jx-couriers__pager button:disabled {
        opacity: 0.5;
        cursor: default;
      }
      .jx-couriers__pageinfo {
        color: var(--text-muted);
      }
    `,
  ],
})
export class AdminEntregadoresPage implements OnInit {
  private readonly kyc = inject(AdminKycService);
  private readonly router = inject(Router);

  protected readonly columns: DataTableColumn[] = [
    { key: 'full_name', label: 'Entregador', sortable: true },
    { key: 'cpf_masked', label: 'CPF' },
    { key: 'kyc_level', label: 'Validação' },
    { key: 'status_label', label: 'Status', sortable: true },
  ];
  protected readonly trackById = (item: unknown) => (item as CourierRow).id;

  private readonly items = signal<CourierRow[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly filter = signal<'pending_kyc' | 'all'>('pending_kyc');
  protected readonly query = signal('');
  protected readonly page = signal(0);
  private readonly sortKey = signal<string | null>(null);
  private readonly sortDir = signal<SortDir>('none');

  /** Filtro (busca) + ordenação client-side sobre os itens carregados. */
  private readonly view = computed<CourierRow[]>(() => {
    const q = this.query().trim().toLowerCase();
    let rows = this.items();
    if (q) {
      rows = rows.filter(
        (c) =>
          c.full_name.toLowerCase().includes(q) ||
          c.cpf_masked.toLowerCase().includes(q)
      );
    }
    const key = this.sortKey();
    const dir = this.sortDir();
    if (key && dir !== 'none') {
      const mult = dir === 'asc' ? 1 : -1;
      const cell = (r: CourierRow): string =>
        String((r as unknown as Record<string, unknown>)[key] ?? '');
      rows = [...rows].sort((a, b) => cell(a).localeCompare(cell(b), 'pt-BR') * mult);
    }
    return rows;
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.view().length / PAGE_SIZE))
  );
  protected readonly paged = computed<CourierRow[]>(() => {
    const start = this.page() * PAGE_SIZE;
    return this.view().slice(start, start + PAGE_SIZE);
  });
  protected readonly tableState = computed<DataTableState>(() => {
    if (this.loading()) return 'loading';
    if (this.error()) return 'error';
    return this.view().length === 0 ? 'empty' : 'ready';
  });

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    this.page.set(0);
    try {
      const status = this.filter() === 'pending_kyc' ? 'pending_kyc' : undefined;
      const list = await this.kyc.listCouriers(status);
      this.items.set(list.items.map((c) => ({ ...c, status_label: statusLabel(c.status) })));
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected onSearch(e: Event): void {
    this.query.set((e.target as HTMLInputElement).value);
    this.page.set(0);
  }

  protected setFilter(value: 'pending_kyc' | 'all'): void {
    this.filter.set(value);
    void this.reload();
  }

  protected onSort(e: { key: string; dir: SortDir }): void {
    this.sortKey.set(e.key);
    this.sortDir.set(e.dir);
    this.page.set(0);
  }

  protected prevPage(): void {
    this.page.update((p) => Math.max(0, p - 1));
  }
  protected nextPage(): void {
    this.page.update((p) => Math.min(this.totalPages() - 1, p + 1));
  }

  protected open(c: CourierRow): void {
    if (c.status === 'pending_kyc') {
      void this.router.navigate(['/admin/kyc', c.id]);
    } else {
      void this.router.navigate(['/admin/entregadores', c.id]);
    }
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending_kyc: 'Em análise',
    active: 'Ativo',
    suspended: 'Suspenso',
    banned: 'Banido',
  };
  return map[status] ?? status;
}
