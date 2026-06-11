import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '../../shared/components/data-table/data-table.component';
import {
  AreaOverviewRow,
  PlatformAdminService,
  RevenueShare,
} from './platform-admin.service';

/**
 * Tela 23 — Visão geral da plataforma (UI-SPEC §Tela 23 / D-06).
 *
 * KPIs agregados (áreas, entregadores, lojas, entregas) em mono + lista de áreas
 * (jx-data-table) com o repasse configurado exibido como badge info "% parametrizado".
 * O repasse é só config — NÃO move dinheiro (D-07). Leitura cross-área auditada no
 * backend. Tokens semânticos; AA nos 2 temas. pt-BR.
 */
@Component({
  selector: 'jx-plataforma-visao-geral',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent],
  templateUrl: './visao-geral.page.html',
  styleUrl: './visao-geral.page.scss',
})
export class PlataformaVisaoGeralPage implements OnInit {
  private readonly service = inject(PlatformAdminService);

  protected readonly state = signal<DataTableState>('loading');
  protected readonly areas = signal<AreaOverviewRow[]>([]);
  protected readonly revenueShares = signal<Record<number, number | null>>({});

  protected readonly columns: DataTableColumn[] = [
    { key: 'name', label: 'Área' },
    { key: 'couriers', label: 'Entregadores', numeric: true },
    { key: 'merchants', label: 'Lojas', numeric: true },
    { key: 'deliveries', label: 'Entregas', numeric: true },
    { key: 'revenue_share', label: 'Repasse' },
  ];

  // KPIs agregados (mono) — somatórios das áreas.
  protected readonly totalAreas = computed(() => this.areas().length);
  protected readonly totalCouriers = computed(() =>
    this.areas().reduce((acc, a) => acc + a.couriers, 0),
  );
  protected readonly totalMerchants = computed(() =>
    this.areas().reduce((acc, a) => acc + a.merchants, 0),
  );
  protected readonly totalDeliveries = computed(() =>
    this.areas().reduce((acc, a) => acc + a.deliveries, 0),
  );

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const rows = await this.service.overview();
      this.areas.set(rows);
      this.state.set(rows.length === 0 ? 'empty' : 'ready');
      // Carrega o repasse de cada área em paralelo (config; tolera 404 → sem valor).
      const entries = await Promise.all(
        rows.map(async (a): Promise<[number, number | null]> => {
          try {
            const rs: RevenueShare | null = await this.service.getRevenueShare(
              a.area_id,
            );
            return [a.area_id, rs ? rs.share_pct : null];
          } catch {
            return [a.area_id, null];
          }
        }),
      );
      this.revenueShares.set(Object.fromEntries(entries));
    } catch {
      this.state.set('error');
    }
  }

  protected revenueLabel(areaId: number): string {
    const pct = this.revenueShares()[areaId];
    if (pct == null) {
      return 'Não parametrizado';
    }
    return `${pct.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}% parametrizado`;
  }

  protected hasRevenue(areaId: number): boolean {
    return this.revenueShares()[areaId] != null;
  }

  protected formatInt(n: number): string {
    return n.toLocaleString('pt-BR');
  }

  protected trackArea = (item: unknown): unknown =>
    (item as AreaOverviewRow).area_id;
}
