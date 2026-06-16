import { HttpClient } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '../../../shared/state';

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

/**
 * Lojas da área (F2.4). Lista as lojas com documento mascarado (TH-06) — consome
 * GET /v1/admin/merchants (area-scoped pelo token). Tokens only.
 */
@Component({
  selector: 'jx-admin-lojas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [EmptyStateComponent, ErrorStateComponent, LoadingSkeletonComponent],
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
      @if (loading()) {
        <jx-loading-skeleton />
      } @else if (error()) {
        <jx-error-state message="Não foi possível carregar as lojas." (retry)="reload()" />
      } @else if (!items().length) {
        <jx-empty-state icon="◫" title="Nenhuma loja" message="As lojas da área aparecem aqui." />
      } @else {
        <table class="jx-lojas__tbl">
          <thead>
            <tr>
              <th>Loja</th>
              <th>Documento</th>
              <th>Categoria</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            @for (m of filtered(); track m.id) {
              <tr>
                <td>{{ m.trade_name }}</td>
                <td class="jx-lojas__mono">{{ m.document_masked }}</td>
                <td>{{ m.category ?? '—' }}</td>
                <td>{{ statusLabel(m.status) }}</td>
              </tr>
            }
          </tbody>
        </table>
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
      .jx-lojas__tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: var(--jx-text-sm);
      }
      .jx-lojas__tbl th {
        text-align: left;
        padding: var(--jx-space-2);
        border-bottom: 1px solid var(--border);
        font-size: var(--jx-text-xs);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
      }
      .jx-lojas__tbl td {
        padding: var(--jx-space-2);
        border-bottom: 1px solid var(--surface-sunken);
      }
      .jx-lojas__mono {
        font-family: var(--jx-font-mono);
      }
    `,
  ],
})
export class AdminLojasPage implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<MerchantListItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly query = signal('');

  protected readonly filtered = computed<MerchantListItem[]>(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return this.items();
    return this.items().filter(
      (m) =>
        m.trade_name.toLowerCase().includes(q) ||
        m.document_masked.toLowerCase().includes(q)
    );
  });

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected onSearch(e: Event): void {
    this.query.set((e.target as HTMLInputElement).value);
  }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    try {
      const page = await firstValueFrom(
        this.http.get<MerchantListOut>('/v1/admin/merchants')
      );
      this.items.set(page.items);
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected statusLabel(status: string): string {
    const map: Record<string, string> = {
      active: 'Ativa',
      pending_payment: 'Aguardando pagamento',
      pending_validation: 'Em validação',
      suspended: 'Suspensa',
    };
    return map[status] ?? status;
  }
}
