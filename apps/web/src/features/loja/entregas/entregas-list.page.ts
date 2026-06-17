import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { DeliveryRowComponent } from '@jaxego/shared/components/delivery-row/delivery-row.component';
import { DeliveryService } from './delivery.service';
import { DeliveryListItem } from '@jaxego/shared/models/delivery.models';

/**
 * Tela 14 — store delivery list (F-03 / UI-SPEC §4.1). `jx-data-table` +
 * `jx-delivery-row`: filter by state/payment, state badge, per-row action
 * (Cancelar ONLY in CRIADA — zero cost pre-acceptance, D-03). Loading/empty/error
 * are embedded in the table. The recipient phone is never shown in the list (LGPD);
 * the list is paginated server-side (no N+1). Tokens only — no hex.
 */
@Component({
  selector: 'jx-loja-entregas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, DataTableComponent, DeliveryRowComponent],
  templateUrl: './entregas-list.page.html',
  styleUrl: './entregas-list.page.scss',
})
export class EntregasListPage implements OnInit {
  private readonly service = inject(DeliveryService);
  private readonly router = inject(Router);

  protected readonly columns: DataTableColumn[] = [
    { key: 'num', label: 'Nº' },
    { key: 'date', label: 'Data' },
    { key: 'recipient', label: 'Destinatário' },
    { key: 'freight', label: 'Frete', numeric: true },
    { key: 'payment', label: 'Pagamento' },
    { key: 'state', label: 'Status' },
  ];

  protected readonly rows = signal<DeliveryListItem[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');
  protected readonly total = signal(0);

  protected stateFilter = '';
  protected paymentFilter = '';

  protected readonly trackById = (item: unknown) => (item as DeliveryListItem).id;

  ngOnInit(): void {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.tableState.set('loading');
    try {
      const page = await this.service.list({
        state: this.stateFilter || undefined,
        paymentMethod: this.paymentFilter || undefined,
      });
      this.rows.set(page.items);
      this.total.set(page.total);
      this.tableState.set(page.items.length === 0 ? 'empty' : 'ready');
    } catch {
      this.tableState.set('error');
    }
  }

  protected hasFilters(): boolean {
    return !!this.stateFilter || !!this.paymentFilter;
  }

  protected clearFilters(): void {
    this.stateFilter = '';
    this.paymentFilter = '';
    void this.load();
  }

  protected async onCancel(item: DeliveryListItem): Promise<void> {
    const ok = window.confirm(
      `Cancelar a entrega ${item.public_token.slice(0, 6)}? ` +
        'Como ninguém aceitou ainda, não há cobrança.',
    );
    if (!ok) {
      return;
    }
    const done = await this.service.cancel(item.id, 'Cancelada pela loja antes do aceite');
    if (done) {
      void this.load();
    }
  }

  protected onView(item: DeliveryListItem): void {
    void this.router.navigate(['/loja/entregas', item.id]);
  }

  protected goNova(): void {
    void this.router.navigate(['/loja/entregas/nova']);
  }
}
