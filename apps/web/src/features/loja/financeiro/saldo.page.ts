import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { MoneyComponent, type MoneySign } from '@jaxego/shared/components/money/money.component';
import { ErrorStateComponent } from '@jaxego/shared/state/error-state.component';

interface CreditLedgerEntry {
  id: number;
  delivery_id: number | null;
  kind: 'reconciliation' | 'consumption' | 'reversal';
  amount_cents: number;
  reason: string | null;
  created_at: string | null;
}

/**
 * Saldo/crédito da loja (extrato) — sobra/falta apurada na finalização das
 * entregas `platform_pix` (preço do entregador vs. valor pago no PIX) e
 * consumo quando a loja escolhe usar saldo como desconto numa entrega nova.
 * Espelha `apps/api/app/merchants/credit.py` + `GET /v1/merchants/credit-balance`
 * e `GET /v1/merchants/credit-ledger`.
 */
@Component({
  selector: 'jx-loja-saldo-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, MoneyComponent, ErrorStateComponent],
  templateUrl: './saldo.page.html',
  styleUrl: './saldo.page.scss',
})
export class LojaSaldoPage {
  private readonly http = inject(HttpClient);

  protected readonly balanceCents = signal(0);
  protected readonly balanceState = signal<'loading' | 'ready' | 'error'>('loading');

  protected readonly entries = signal<CreditLedgerEntry[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');

  protected readonly columns: DataTableColumn[] = [
    { key: 'created_at', label: 'Data' },
    { key: 'reason', label: 'Motivo' },
    { key: 'amount_cents', label: 'Valor', numeric: true },
  ];

  constructor() {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.balanceState.set('loading');
    this.tableState.set('loading');
    await Promise.all([this.loadBalance(), this.loadLedger()]);
  }

  private async loadBalance(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ balance_cents: number }>('/v1/merchants/credit-balance')
      );
      this.balanceCents.set(res.balance_cents);
      this.balanceState.set('ready');
    } catch {
      this.balanceState.set('error');
    }
  }

  private async loadLedger(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ items: CreditLedgerEntry[] }>('/v1/merchants/credit-ledger')
      );
      this.entries.set(res.items);
      this.tableState.set(res.items.length === 0 ? 'empty' : 'ready');
    } catch {
      this.tableState.set('error');
    }
  }

  protected get balanceSign(): MoneySign {
    const c = this.balanceCents();
    if (c > 0) return 'credit';
    if (c < 0) return 'debit';
    return 'none';
  }

  protected entrySign(entry: CreditLedgerEntry): MoneySign {
    return entry.amount_cents >= 0 ? 'credit' : 'debit';
  }

  /** jx-money espera a magnitude (sem sinal) — `sign` já cuida do +/−. */
  protected entryAbsCents(entry: CreditLedgerEntry): number {
    return Math.abs(entry.amount_cents);
  }

  protected kindLabel(kind: string): string {
    if (kind === 'consumption') return 'Desconto usado';
    if (kind === 'reversal') return 'Saldo devolvido (cancelamento)';
    return 'Ajuste de entrega';
  }

  protected formatDate(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  protected trackEntry = (item: unknown): unknown => (item as CreditLedgerEntry).id;
}
