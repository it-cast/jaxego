import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

interface DeliveryItem {
  id: number;
  state: string;
  pickup_address: string;
  dropoff_address: string | null;
  price_cents: number | null;
  courier_name: string | null;
  created_at: string | null;
}

const PAGE_SIZE = 20;

@Component({
  selector: 'jx-equipe-entregas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
  template: `
    <h1 class="jx-eq-del__title">Entregas da equipe</h1>

    <div class="jx-eq-del__filters">
      <input
        type="search"
        class="jx-eq-del__input"
        placeholder="Buscar por entregador..."
        [value]="filterCourier()"
        (input)="filterCourier.set($any($event.target).value); resetPage()"
      />
      <select class="jx-eq-del__select" [value]="filterStatus()" (change)="filterStatus.set($any($event.target).value); resetPage()">
        <option value="all">Todos os status</option>
        <option value="CRIADA">Procurando</option>
        <option value="ACEITA">Aceita</option>
        <option value="COLETADA">A caminho</option>
        <option value="ENTREGUE">Entregue</option>
        <option value="FINALIZADA">Finalizada</option>
        <option value="CANCELADA">Cancelada</option>
      </select>
      <input
        type="date"
        class="jx-eq-del__input jx-eq-del__input--date"
        [value]="filterDate()"
        (input)="filterDate.set($any($event.target).value); resetPage()"
      />
      @if (filterCourier() || filterStatus() !== 'all' || filterDate()) {
        <button type="button" class="jx-eq-del__clear" (click)="clearFilters()">Limpar</button>
      }
    </div>

    @if (loading()) {
      <p>Carregando...</p>
    } @else if (filtered().length === 0) {
      <p class="jx-eq-del__empty">Nenhuma entrega encontrada.</p>
    } @else {
      <table class="jx-eq-del__table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Entregador</th>
            <th>Coleta</th>
            <th>Entrega</th>
            <th>Valor</th>
            <th>Status</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          @for (d of paged(); track d.id) {
            <tr>
              <td class="jx-eq-del__mono">#{{ d.id }}</td>
              <td>{{ d.courier_name ?? '—' }}</td>
              <td>{{ d.pickup_address }}</td>
              <td>{{ d.dropoff_address ?? '—' }}</td>
              <td class="jx-eq-del__mono">{{ d.price_cents != null ? 'R$ ' + (d.price_cents / 100).toFixed(2).replace('.', ',') : '—' }}</td>
              <td><span class="jx-eq-del__state">{{ stateLabel(d.state) }}</span></td>
              <td class="jx-eq-del__mono">{{ formatDate(d.created_at) }}</td>
            </tr>
          }
        </tbody>
      </table>

      @if (totalPages() > 1) {
        <div class="jx-eq-del__pagination">
          <button [disabled]="page() === 0" (click)="page.set(page() - 1)">Anterior</button>
          <span>{{ page() + 1 }} de {{ totalPages() }}</span>
          <button [disabled]="page() >= totalPages() - 1" (click)="page.set(page() + 1)">Próxima</button>
        </div>
      }
    }
  `,
  styles: [`
    .jx-eq-del__title { margin: 0 0 var(--jx-space-4); font-family: var(--jx-font-display); font-size: 24px; font-weight: 800; color: var(--text); }
    .jx-eq-del__filters { display: flex; gap: var(--jx-space-2); flex-wrap: wrap; margin-bottom: var(--jx-space-3); }
    .jx-eq-del__input { min-height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; color: var(--text); background: var(--surface, #fff); min-width: 200px; }
    .jx-eq-del__input--date { min-width: 160px; }
    .jx-eq-del__select { min-height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; color: var(--text); background: var(--surface, #fff); }
    .jx-eq-del__clear { min-height: 40px; padding: 0 14px; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--text-muted); font-size: 13px; font-weight: 600; cursor: pointer; }
    .jx-eq-del__clear:hover { color: var(--error); border-color: var(--error); }
    .jx-eq-del__empty { color: var(--text-muted); }
    .jx-eq-del__table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .jx-eq-del__table th { text-align: left; padding: var(--jx-space-2) var(--jx-space-3); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); border-bottom: 2px solid var(--border); }
    .jx-eq-del__table td { padding: var(--jx-space-2) var(--jx-space-3); border-bottom: 1px solid var(--border, #eee); color: var(--text); }
    .jx-eq-del__mono { font-family: var(--jx-font-mono, monospace); font-size: 13px; }
    .jx-eq-del__state { font-size: 12px; font-weight: 600; }
    .jx-eq-del__pagination { display: flex; align-items: center; justify-content: center; gap: var(--jx-space-3); padding: var(--jx-space-3) 0; }
    .jx-eq-del__pagination button { min-height: 36px; padding: 0 var(--jx-space-3); border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text); font-size: 13px; cursor: pointer; }
    .jx-eq-del__pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
    .jx-eq-del__pagination span { font-size: 13px; color: var(--text-muted); font-weight: 600; }
  `],
})
export class EquipeEntregasPage implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly loading = signal(true);
  protected readonly deliveriesAll = signal<DeliveryItem[]>([]);
  protected readonly page = signal(0);

  protected readonly filterCourier = signal('');
  protected readonly filterStatus = signal('all');
  protected readonly filterDate = signal('');

  protected readonly filtered = computed(() => {
    let list = this.deliveriesAll();
    const q = this.filterCourier().trim().toLowerCase();
    if (q) list = list.filter(d => (d.courier_name ?? '').toLowerCase().includes(q));
    const status = this.filterStatus();
    if (status !== 'all') list = list.filter(d => d.state === status);
    const date = this.filterDate();
    if (date) list = list.filter(d => (d.created_at ?? '').startsWith(date));
    return list;
  });

  protected readonly totalPages = computed(() => Math.max(1, Math.ceil(this.filtered().length / PAGE_SIZE)));
  protected readonly paged = computed(() => {
    const s = this.page() * PAGE_SIZE;
    return this.filtered().slice(s, s + PAGE_SIZE);
  });

  async ngOnInit(): Promise<void> { await this.load(); }

  private async load(): Promise<void> {
    this.loading.set(true);
    const res = await firstValueFrom(
      this.http.get<{ items: DeliveryItem[]; total: number }>('/v1/team-admin/deliveries', { params: { limit: 500, offset: 0 } })
    );
    this.deliveriesAll.set(res.items);
    this.loading.set(false);
  }

  protected resetPage(): void { this.page.set(0); }

  protected clearFilters(): void {
    this.filterCourier.set('');
    this.filterStatus.set('all');
    this.filterDate.set('');
    this.page.set(0);
  }

  protected stateLabel(s: string): string {
    return { CRIADA: 'Procurando', ACEITA: 'Aceita', COLETADA: 'A caminho', ENTREGUE: 'Entregue', FINALIZADA: 'Finalizada', CANCELADA: 'Cancelada' }[s] ?? s;
  }

  protected formatDate(iso: string | null): string {
    if (!iso) return '—';
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
}
