import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';

interface MerchantListItem {
  id: number;
  trade_name: string;
  account_type: string;
  document_masked: string;
  category: string | null;
  status: string;
  created_at: string | null;
}

interface MerchantListOut {
  items: MerchantListItem[];
  total: number;
  limit: number;
  offset: number;
}

interface MerchantRow extends MerchantListItem {
  status_label: string;
  category_label: string;
}

type SortDir = 'asc' | 'desc' | 'none';
const PAGE_SIZE = 10;

/**
 * Lojas da área (F2.4) com profundidade operacional (MG-2.3): busca + jx-data-table
 * (ordenação por coluna, estados loading/empty/error) + paginação. Documento
 * mascarado (TH-06). Tokens only.
 */
@Component({
  selector: 'jx-admin-lojas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent],
  template: `
    <section class="jx-lojas">
      <header class="jx-lojas__head">
        <h1 class="jx-lojas__title">Lojas</h1>
        <input
          type="search"
          class="jx-lojas__search"
          placeholder="Buscar loja…"
          [value]="query()"
          (input)="onSearch($event)"
          aria-label="Buscar loja"
        />
      </header>

      <jx-data-table
        [columns]="columns"
        [rows]="paged()"
        [state]="tableState()"
        [trackBy]="trackById"
        caption="Lojas da área"
        emptyIcon="◫"
        emptyTitle="Nenhuma loja"
        emptyMessage="As lojas da área aparecem aqui."
        errorMessage="Não foi possível carregar as lojas."
        (sortChange)="onSort($event)"
        (retry)="reload()"
      >
        <ng-template #row let-m>
          <td>{{ m.trade_name }}</td>
          <td class="jx-lojas__mono">{{ m.document_masked }}</td>
          <td>{{ m.category_label }}</td>
          <td>{{ m.status_label }}</td>
        </ng-template>
      </jx-data-table>

      @if (totalPages() > 1) {
        <nav class="jx-lojas__pager" aria-label="Paginação">
          <button type="button" (click)="prevPage()" [disabled]="page() === 0">
            ← Anterior
          </button>
          <span class="jx-lojas__pageinfo">
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
      .jx-lojas {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-lojas__head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--jx-space-3);
        flex-wrap: wrap;
      }
      .jx-lojas__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0;
      }
      .jx-lojas__search {
        padding: var(--jx-space-2);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-md);
        background: var(--surface);
        color: var(--text);
        font-size: var(--jx-text-sm);
        min-width: 220px;
      }
      .jx-lojas__mono {
        font-family: var(--jx-font-mono);
      }
      .jx-lojas__pager {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--jx-space-3);
        font-size: var(--jx-text-sm);
      }
      .jx-lojas__pager button {
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        border-radius: var(--jx-radius-sm);
        padding: 6px 12px;
        cursor: pointer;
      }
      .jx-lojas__pager button:disabled {
        opacity: 0.5;
        cursor: default;
      }
      .jx-lojas__pageinfo {
        color: var(--text-muted);
      }
    `,
  ],
})
export class AdminLojasPage implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly columns: DataTableColumn[] = [
    { key: 'trade_name', label: 'Loja', sortable: true },
    { key: 'document_masked', label: 'Documento' },
    { key: 'category_label', label: 'Categoria' },
    { key: 'status_label', label: 'Status', sortable: true },
  ];
  protected readonly trackById = (item: unknown) => (item as MerchantRow).id;

  private readonly items = signal<MerchantRow[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly query = signal('');
  protected readonly page = signal(0);
  private readonly sortKey = signal<string | null>(null);
  private readonly sortDir = signal<SortDir>('none');

  private readonly view = computed<MerchantRow[]>(() => {
    const q = this.query().trim().toLowerCase();
    let rows = this.items();
    if (q) {
      rows = rows.filter(
        (m) =>
          m.trade_name.toLowerCase().includes(q) ||
          m.document_masked.toLowerCase().includes(q)
      );
    }
    const key = this.sortKey();
    const dir = this.sortDir();
    if (key && dir !== 'none') {
      const mult = dir === 'asc' ? 1 : -1;
      const cell = (r: MerchantRow): string =>
        String((r as unknown as Record<string, unknown>)[key] ?? '');
      rows = [...rows].sort((a, b) => cell(a).localeCompare(cell(b), 'pt-BR') * mult);
    }
    return rows;
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.view().length / PAGE_SIZE))
  );
  protected readonly paged = computed<MerchantRow[]>(() => {
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
      const page = await firstValueFrom(
        this.http.get<MerchantListOut>('/v1/admin/merchants')
      );
      this.items.set(
        page.items.map((m) => ({
          ...m,
          status_label: statusLabel(m.status),
          category_label: m.category ?? '—',
        }))
      );
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
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    active: 'Ativa',
    pending_payment: 'Aguardando pagamento',
    pending_validation: 'Em validação',
    suspended: 'Suspensa',
  };
  return map[status] ?? status;
}
