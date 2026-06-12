import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '../../../shared/components/data-table/data-table.component';
import { InvoiceSummaryComponent } from '../../../shared/components/invoice-summary/invoice-summary.component';
import { MoneyComponent } from '../../../shared/components/money/money.component';
import { ErrorStateComponent } from '../../../shared/state/error-state.component';
import { Invoice, InvoiceLine, LojaFinanceiroService } from './financeiro.service';

/**
 * Tela 15 — Fatura mensal da loja (UI-SPEC §15 / D-06 / REQ-037).
 *
 * Mostra a fatura mais recente (jx-invoice-summary: competência, total mono,
 * vencimento, status, CTA pagar), as linhas (jx-data-table: entrega, descrição,
 * taxa) e um banner de vencimento quando a fatura está vencida ("Novas entregas
 * ficam bloqueadas 7 dias após o vencimento."). Pagar reusa o fluxo de checkout
 * (payment-checkout-ux) via o serviço. Estados loading/empty/error em todas as
 * superfícies. Rota lazy. Tokens semânticos; zero hex; AA nos 2 temas (DEC-001).
 */
@Component({
  selector: 'jx-loja-fatura-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    InvoiceSummaryComponent,
    DataTableComponent,
    MoneyComponent,
    ErrorStateComponent,
  ],
  templateUrl: './fatura.page.html',
  styleUrl: './fatura.page.scss',
})
export class LojaFaturaPage {
  private readonly service = inject(LojaFinanceiroService);

  protected readonly pageState = signal<DataTableState>('loading');
  protected readonly invoices = signal<Invoice[]>([]);
  protected readonly current = signal<Invoice | null>(null);

  protected readonly linesState = signal<DataTableState>('loading');
  protected readonly lines = signal<InvoiceLine[]>([]);

  protected readonly paying = signal(false);
  protected readonly payError = signal<string | null>(null);
  protected readonly payDone = signal(false);

  protected readonly lineColumns: DataTableColumn[] = [
    { key: 'description', label: 'Entrega' },
    { key: 'amount_cents', label: 'Taxa', numeric: true },
  ];

  /** A fatura atual está vencida → banner de bloqueio (F-03 E5). */
  protected readonly isOverdue = computed(() => this.current()?.status === 'overdue');

  constructor() {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.pageState.set('loading');
    this.payError.set(null);
    try {
      const invoices = await this.service.invoices();
      this.invoices.set(invoices);
      if (invoices.length === 0) {
        this.current.set(null);
        this.pageState.set('empty');
        return;
      }
      // A mais recente vem primeiro (order_by competence desc no backend).
      const current = invoices[0];
      this.current.set(current);
      this.pageState.set('ready');
      await this.loadLines(current.id);
    } catch {
      this.pageState.set('error');
    }
  }

  protected async loadLines(invoiceId: number): Promise<void> {
    this.linesState.set('loading');
    try {
      const lines = await this.service.invoiceLines(invoiceId);
      this.lines.set(lines);
      this.linesState.set(lines.length === 0 ? 'empty' : 'ready');
    } catch {
      this.linesState.set('error');
    }
  }

  protected async pay(invoiceId: number): Promise<void> {
    this.paying.set(true);
    this.payError.set(null);
    this.payDone.set(false);
    try {
      const updated = await this.service.payInvoice(invoiceId);
      this.current.set(updated);
      this.invoices.update((list) =>
        list.map((inv) => (inv.id === updated.id ? updated : inv)),
      );
      this.payDone.set(true);
    } catch {
      this.payError.set(
        'Não conseguimos concluir o pagamento agora. Tente de novo em instantes.',
      );
    } finally {
      this.paying.set(false);
    }
  }

  protected trackLine = (item: unknown): unknown => (item as InvoiceLine).id;
}
