import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { StateBadgeComponent } from '@jaxego/shared/components/state-badge/state-badge.component';
import { WarnBannerComponent } from '@jaxego/shared/state';
import { DeliveryService } from '../entregas/delivery.service';
import { DeliveryListItem } from '@jaxego/shared/models/delivery.models';
import { formatBrl } from '@jaxego/shared/util/money';

interface Kpi {
  label: string;
  value: string;
}

/**
 * Tela 11 — store dashboard (UI-SPEC §4.2). KPIs in mono (from the API, nothing
 * hardcoded), an "em curso agora" table (only CRIADA rows reach it in Phase 7),
 * the primary "+ Nova entrega" CTA, and the invoice banner SLOT (hidden — Phase
 * 11). H1 carries one Fraunces-italic word (ui-ux-pro-max). Tokens only — no hex.
 */
@Component({
  selector: 'jx-loja-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, StateBadgeComponent, WarnBannerComponent],
  templateUrl: './dashboard.page.html',
  styleUrl: './dashboard.page.scss',
})
export class LojaDashboardPage implements OnInit {
  private readonly service = inject(DeliveryService);
  private readonly router = inject(Router);

  protected readonly columns: DataTableColumn[] = [
    { key: 'num', label: 'Entrega' },
    { key: 'recipient', label: 'Destinatário' },
    { key: 'state', label: 'Status' },
    { key: 'payment', label: 'Pagamento' },
  ];

  protected readonly inProgress = signal<DeliveryListItem[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');
  protected readonly kpis = signal<Kpi[]>([]);
  /** Invoice banner hook (Phase 11) — kept hidden in Phase 7. */
  protected readonly showInvoiceBanner = signal(false);

  protected readonly trackById = (item: unknown) => (item as DeliveryListItem).id;

  ngOnInit(): void {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.tableState.set('loading');
    try {
      // "Em curso" = non-terminal states; in Phase 7 only CRIADA is produced.
      const page = await this.service.list({ state: 'CRIADA' });
      this.inProgress.set(page.items);
      this.tableState.set(page.items.length === 0 ? 'empty' : 'ready');
      this.computeKpis(page.items, page.total);
    } catch {
      this.tableState.set('error');
    }
  }

  private computeKpis(items: DeliveryListItem[], total: number): void {
    const today = new Date().toISOString().slice(0, 10);
    const todays = items.filter((d) => (d.created_at ?? '').startsWith(today));
    const freightToday = todays.reduce((sum, d) => sum + (d.price_cents ?? 0), 0);
    this.kpis.set([
      { label: 'Entregas em curso', value: String(items.length) },
      { label: 'Entregas hoje', value: String(todays.length) },
      { label: 'Fretes hoje', value: formatBrl(freightToday / 100) },
      { label: 'Entregas no mês', value: String(total) },
    ]);
  }

  protected goNova(): void {
    void this.router.navigate(['/loja/entregas/nova']);
  }

  protected onView(item: DeliveryListItem): void {
    void this.router.navigate(['/loja/entregas', item.id]);
  }

  protected shortToken(item: DeliveryListItem): string {
    return '#' + item.public_token.slice(0, 6);
  }

  protected paymentLabel(item: DeliveryListItem): string {
    return { direct: 'Direto', pix: 'PIX', card: 'Cartão' }[item.payment_method];
  }
}
