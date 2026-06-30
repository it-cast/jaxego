import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStar, faChevronLeft, faChevronRight } from '@fortawesome/free-solid-svg-icons';
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

const PAGE_SIZE = 20;

/**
 * Tela 24 — Entregadores e lojas cross-área + score (UI-SPEC §Tela 24 / D-06).
 */
@Component({
  selector: 'jx-plataforma-pessoas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    DataTableComponent,
    NoticeComponent,
    ScoreBadgeComponent,
    ScoreBreakdownComponent,
    FaIconComponent,
  ],
  templateUrl: './pessoas.page.html',
  styleUrl: './pessoas.page.scss',
})
export class PlataformaPessoasPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(PlatformAdminService);

  protected readonly tab = signal<Tab>('couriers');
  protected readonly iconStar = faStar;
  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;
  protected readonly pageSize = PAGE_SIZE;

  protected readonly searchForm = this.fb.nonNullable.group({
    q: this.fb.nonNullable.control(''),
    areaId: this.fb.nonNullable.control<number | null>(null),
  });

  // --- Entregadores ---------------------------------------------------------
  protected readonly couriersState = signal<DataTableState>('loading');
  protected readonly couriers = signal<CourierSearchRow[]>([]);
  protected readonly courierPage = signal(1);
  protected readonly courierHasNext = signal(false);

  protected readonly courierColumns: DataTableColumn[] = [
    { key: 'full_name', label: 'Nome' },
    { key: 'area_name', label: 'Área' },
    { key: 'status', label: 'Situação' },
    { key: 'avg_stars', label: 'Avaliação' },
  ];

  // --- Lojas ----------------------------------------------------------------
  protected readonly merchantsState = signal<DataTableState>('loading');
  protected readonly merchants = signal<MerchantSearchRow[]>([]);
  protected readonly merchantPage = signal(1);
  protected readonly merchantHasNext = signal(false);

  protected readonly merchantColumns: DataTableColumn[] = [
    { key: 'name', label: 'Loja' },
    { key: 'area_name', label: 'Área' },
    { key: 'status', label: 'Situação' },
  ];

  // --- Breakdown de score (drawer) -----------------------------------------
  protected readonly selectedCourier = signal<CourierSearchRow | null>(null);
  protected readonly scoreState = signal<'idle' | 'loading' | 'ready' | 'error'>('idle');
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
    const params = { q: q.trim() || undefined, areaId: areaId ?? undefined };

    if (this.tab() === 'couriers') {
      this.courierPage.set(1);
      await this.loadCouriers(params, 1);
    } else {
      this.merchantPage.set(1);
      await this.loadMerchants(params, 1);
    }
  }

  protected async courierGoTo(delta: number): Promise<void> {
    const next = this.courierPage() + delta;
    const { q, areaId } = this.searchForm.getRawValue();
    this.courierPage.set(next);
    await this.loadCouriers({ q: q.trim() || undefined, areaId: areaId ?? undefined }, next);
  }

  protected async merchantGoTo(delta: number): Promise<void> {
    const next = this.merchantPage() + delta;
    const { q, areaId } = this.searchForm.getRawValue();
    this.merchantPage.set(next);
    await this.loadMerchants({ q: q.trim() || undefined, areaId: areaId ?? undefined }, next);
  }

  private async loadCouriers(
    params: { q?: string; areaId?: number },
    page: number,
  ): Promise<void> {
    this.couriersState.set('loading');
    try {
      const rows = await this.service.searchCouriers({
        ...params,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      });
      this.couriers.set(rows);
      this.courierHasNext.set(rows.length === PAGE_SIZE);
      this.couriersState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.couriersState.set('error');
    }
  }

  private async loadMerchants(
    params: { q?: string; areaId?: number },
    page: number,
  ): Promise<void> {
    this.merchantsState.set('loading');
    try {
      const rows = await this.service.searchMerchants({
        ...params,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      });
      this.merchants.set(rows);
      this.merchantHasNext.set(rows.length === PAGE_SIZE);
      this.merchantsState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.merchantsState.set('error');
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
      pending_kyc: 'Aguardando documentos',
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
