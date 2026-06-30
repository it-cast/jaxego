import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { DataTableColumn, DataTableComponent, DataTableState } from '@jaxego/shared/components/data-table/data-table.component';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faChevronLeft, faChevronRight } from '@fortawesome/free-solid-svg-icons';
import { EquipeKycService, CourierListItem } from './equipe-kyc.service';

interface CourierRow extends CourierListItem { status_label: string; }
const PAGE_SIZE = 20;

@Component({
  selector: 'jx-equipe-entregadores',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, FaIconComponent],
  template: `
    <section class="jx-couriers">
      <header class="jx-couriers__head">
        <h1 class="jx-couriers__title">Entregadores</h1>
        <div class="jx-couriers__seg" role="tablist">
          <button type="button" role="tab" [class.jx-couriers__seg-btn--on]="filter() === 'pending'" class="jx-couriers__seg-btn" (click)="setFilter('pending')">Fila de validação</button>
          <button type="button" role="tab" [class.jx-couriers__seg-btn--on]="filter() === 'all'" class="jx-couriers__seg-btn" (click)="setFilter('all')">Todos</button>
        </div>
        <input type="search" class="jx-couriers__search" placeholder="Buscar por nome..." [value]="query()" (input)="onSearch($event)" />
      </header>

      <jx-data-table
        [columns]="columns"
        [rows]="paged()"
        [state]="tableState()"
        [hasActions]="true"
        [trackBy]="trackById"
        caption="Entregadores da equipe"
        emptyIcon=""
        emptyTitle="Nenhum entregador"
        emptyMessage="Quando um entregador se cadastrar na sua equipe, aparece aqui."
        errorMessage="Não foi possível carregar."
        (retry)="reload()"
      >
        <ng-template #row let-c>
          <td>{{ c.full_name }}</td>
          <td>{{ vehicleLabel(c.vehicle_type) }}</td>
          <td>{{ c.status_label }}</td>
          <td>{{ c.is_online ? 'Online' : 'Offline' }}</td>
          <td>
            <button type="button" class="jx-couriers__open" (click)="open(c)">
              {{ c.status === 'pending_kyc' ? 'Revisar' : 'Abrir' }}
            </button>
          </td>
        </ng-template>
      </jx-data-table>

      @if (totalPages() > 1) {
        <nav class="jx-couriers__pager" aria-label="Paginação de entregadores">
          <button class="jx-couriers__pager-btn" (click)="prevPage()" [disabled]="page() === 0" aria-label="Página anterior">
            <fa-icon [icon]="iconPrev" aria-hidden="true" /> Anterior
          </button>
          <span class="jx-couriers__pager-info">Página {{ page() + 1 }} de {{ totalPages() }}</span>
          <button class="jx-couriers__pager-btn" (click)="nextPage()" [disabled]="page() >= totalPages() - 1" aria-label="Próxima página">
            Próxima <fa-icon [icon]="iconNext" aria-hidden="true" />
          </button>
        </nav>
      }
    </section>
  `,
  styles: [`
    .jx-couriers { display: flex; flex-direction: column; gap: var(--jx-space-3); }
    .jx-couriers__head { display: flex; align-items: center; justify-content: space-between; gap: var(--jx-space-3); flex-wrap: wrap; }
    .jx-couriers__title { font-family: var(--jx-font-display); font-size: var(--jx-text-2xl); margin: 0; }
    .jx-couriers__seg { display: inline-flex; background: var(--surface-sunken); border-radius: var(--jx-radius-md); padding: 3px; gap: 2px; }
    .jx-couriers__seg-btn { border: 0; background: transparent; padding: var(--jx-space-1) var(--jx-space-3); border-radius: var(--jx-radius-sm); font-size: var(--jx-text-sm); font-weight: 500; color: var(--text-muted); cursor: pointer; }
    .jx-couriers__seg-btn--on { background: var(--surface); color: var(--text); }
    .jx-couriers__search { padding: var(--jx-space-2); border: 1px solid var(--border); border-radius: var(--jx-radius-md); background: var(--surface); color: var(--text); font-size: var(--jx-text-sm); min-width: 240px; }
    .jx-couriers__open { border: 1px solid var(--border); background: var(--surface); color: var(--brand); border-radius: var(--jx-radius-sm); padding: 4px 12px; font-weight: 600; cursor: pointer; }
    .jx-couriers__pager { display: flex; align-items: center; justify-content: center; gap: var(--jx-space-3); padding: var(--jx-space-2) 0; }
    .jx-couriers__pager-btn { display: inline-flex; align-items: center; gap: var(--jx-space-2); min-height: 36px; padding: 0 var(--jx-space-3); background: var(--surface-elevated); border: 1px solid var(--border-strong); border-radius: var(--jx-radius-lg); color: var(--text); font-family: var(--jx-font-display); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-medium); cursor: pointer; transition: background 120ms ease; }
    .jx-couriers__pager-btn:hover:not(:disabled) { background: var(--surface-sunken); }
    .jx-couriers__pager-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .jx-couriers__pager-btn:focus-visible { outline: none; box-shadow: var(--focus-ring); }
    .jx-couriers__pager-info { font-size: var(--jx-text-sm); color: var(--text-muted); min-width: 100px; text-align: center; }
  `],
})
export class EquipeEntregadoresPage implements OnInit {
  private readonly svc = inject(EquipeKycService);
  private readonly router = inject(Router);

  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;

  protected readonly columns: DataTableColumn[] = [
    { key: 'full_name', label: 'Entregador', sortable: true },
    { key: 'vehicle_type', label: 'Veículo' },
    { key: 'status_label', label: 'Status', sortable: true },
    { key: 'is_online', label: 'Disponível' },
  ];
  protected readonly trackById = (item: unknown) => (item as CourierRow).id;

  private readonly items = signal<CourierRow[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly filter = signal<'pending' | 'all'>('pending');
  protected readonly query = signal('');
  protected readonly page = signal(0);

  private readonly view = computed<CourierRow[]>(() => {
    const q = this.query().trim().toLowerCase();
    let rows = this.items();
    if (q) rows = rows.filter(c => c.full_name.toLowerCase().includes(q));
    return rows;
  });

  protected readonly totalPages = computed(() => Math.max(1, Math.ceil(this.view().length / PAGE_SIZE)));
  protected readonly paged = computed(() => { const s = this.page() * PAGE_SIZE; return this.view().slice(s, s + PAGE_SIZE); });
  protected readonly tableState = computed<DataTableState>(() => {
    if (this.loading()) return 'loading';
    if (this.error()) return 'error';
    return this.view().length === 0 ? 'empty' : 'ready';
  });

  async ngOnInit(): Promise<void> { await this.reload(); }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    this.page.set(0);
    try {
      const list = await this.svc.listCouriers();
      let filtered = list;
      if (this.filter() === 'pending') filtered = list.filter(c => c.status === 'pending_kyc');
      this.items.set(filtered.map(c => ({ ...c, status_label: statusLabel(c.status) })));
    } catch { this.error.set(true); }
    finally { this.loading.set(false); }
  }

  protected onSearch(e: Event): void { this.query.set((e.target as HTMLInputElement).value); this.page.set(0); }
  protected setFilter(v: 'pending' | 'all'): void { this.filter.set(v); void this.reload(); }
  protected prevPage(): void { this.page.update(p => Math.max(0, p - 1)); }
  protected nextPage(): void { this.page.update(p => Math.min(this.totalPages() - 1, p + 1)); }

  protected vehicleLabel(v: string): string {
    const map: Record<string, string> = {
      moto: 'Moto',
      bicicleta: 'Bicicleta',
      carro: 'Carro',
      a_pe: 'A pé',
    };
    return map[v] ?? v;
  }

  protected open(c: CourierRow): void {
    void this.router.navigate(['/equipe/entregadores', c.id]);
  }
}

function statusLabel(s: string): string {
  return { pending_kyc: 'Em análise', active: 'Ativo', suspended: 'Suspenso', banned: 'Banido' }[s] ?? s;
}
