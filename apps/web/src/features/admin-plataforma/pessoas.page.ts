import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { NoticeComponent } from '@jaxego/shared/components/notice/notice.component';
import { ScoreBadgeComponent } from '@jaxego/shared/components/score-badge/score-badge.component';
import { ScoreBreakdownComponent } from '@jaxego/shared/components/score-breakdown/score-breakdown.component';
import {
  CourierScore,
  CourierSearchRow,
  MerchantSearchRow,
  PlatformAdminService,
} from './platform-admin.service';

type Tab = 'couriers' | 'merchants';

/**
 * Tela 24 — Entregadores e lojas cross-área + score (UI-SPEC §Tela 24 / D-06).
 *
 * jx-data-table com busca/filtro (search-filter-ux): nome + jx-score-badge para
 * entregadores. Clicar numa linha abre o jx-score-breakdown explicável (ADR-013).
 * Aviso info: "Score não afeta despacho nem cobrança no piloto". A busca cross-área
 * é auditada no backend (TH-02). Filtros são bound (TH-06). Tokens; AA 2 temas. pt-BR.
 */
@Component({
  selector: 'jx-plataforma-pessoas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    DataTableComponent,
    NoticeComponent,
    ScoreBadgeComponent,
    ScoreBreakdownComponent,
  ],
  templateUrl: './pessoas.page.html',
  styleUrl: './pessoas.page.scss',
})
export class PlataformaPessoasPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(PlatformAdminService);

  protected readonly tab = signal<Tab>('couriers');

  protected readonly searchForm = this.fb.nonNullable.group({
    q: this.fb.nonNullable.control(''),
    areaId: this.fb.nonNullable.control<number | null>(null),
  });

  // --- Entregadores ---------------------------------------------------------
  protected readonly couriersState = signal<DataTableState>('loading');
  protected readonly couriers = signal<CourierSearchRow[]>([]);

  protected readonly courierColumns: DataTableColumn[] = [
    { key: 'full_name', label: 'Nome' },
    { key: 'area_id', label: 'Área', numeric: true },
    { key: 'status', label: 'Situação' },
    { key: 'score', label: 'Score' },
  ];

  // --- Lojas ----------------------------------------------------------------
  protected readonly merchantsState = signal<DataTableState>('loading');
  protected readonly merchants = signal<MerchantSearchRow[]>([]);

  protected readonly merchantColumns: DataTableColumn[] = [
    { key: 'name', label: 'Loja' },
    { key: 'area_id', label: 'Área', numeric: true },
    { key: 'status', label: 'Situação' },
  ];

  // --- Breakdown de score (drawer) -----------------------------------------
  protected readonly selectedCourier = signal<CourierSearchRow | null>(null);
  protected readonly scoreState = signal<'idle' | 'loading' | 'ready' | 'error'>(
    'idle',
  );
  protected readonly score = signal<CourierScore | null>(null);

  @ViewChild('breakdownClose')
  private breakdownClose?: ElementRef<HTMLButtonElement>;

  async ngOnInit(): Promise<void> {
    await this.search();
  }

  protected setTab(tab: Tab): void {
    this.tab.set(tab);
    void this.search();
  }

  protected async search(): Promise<void> {
    const { q, areaId } = this.searchForm.getRawValue();
    const params = {
      q: q.trim() || undefined,
      areaId: areaId ?? undefined,
    };
    if (this.tab() === 'couriers') {
      this.couriersState.set('loading');
      try {
        const rows = await this.service.searchCouriers(params);
        this.couriers.set(rows);
        this.couriersState.set(rows.length === 0 ? 'empty' : 'ready');
      } catch {
        this.couriersState.set('error');
      }
    } else {
      this.merchantsState.set('loading');
      try {
        const rows = await this.service.searchMerchants(params);
        this.merchants.set(rows);
        this.merchantsState.set(rows.length === 0 ? 'empty' : 'ready');
      } catch {
        this.merchantsState.set('error');
      }
    }
  }

  protected async openBreakdown(courier: CourierSearchRow): Promise<void> {
    this.selectedCourier.set(courier);
    this.scoreState.set('loading');
    this.score.set(null);
    try {
      const s = await this.service.courierScore(courier.courier_id);
      this.score.set(s);
      this.scoreState.set('ready');
    } catch {
      this.scoreState.set('error');
    }
  }

  protected closeBreakdown(): void {
    this.selectedCourier.set(null);
    this.scoreState.set('idle');
  }

  protected statusLabel(status: string): string {
    const map: Record<string, string> = {
      active: 'Ativo',
      suspended: 'Suspenso',
      banned: 'Banido',
      pending: 'Pendente',
    };
    return map[status] ?? status;
  }

  protected trackCourier = (item: unknown): unknown =>
    (item as CourierSearchRow).courier_id;
  protected trackMerchant = (item: unknown): unknown =>
    (item as MerchantSearchRow).merchant_id;
}
