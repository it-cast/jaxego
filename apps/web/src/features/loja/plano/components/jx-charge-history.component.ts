import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';
import {
  DataTableColumn,
  DataTableComponent,
  type DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { type ChargeHistoryItem, formatCents } from '../billing.service';

interface ChargeRow {
  date: string;
  description: string;
  amount: string;
  status: string;
  statusColor: string;
}

const STATUS_META: Record<string, { label: string; cssVar: string }> = {
  paid: { label: 'PAGA', cssVar: '--success' },
  open: { label: 'EM ABERTO', cssVar: '--warning' },
  failed: { label: 'FALHOU', cssVar: '--error' },
  refunded: { label: 'ESTORNADA', cssVar: '--info' },
  canceled: { label: 'CANCELADA', cssVar: '--text-muted' },
};

/**
 * jx-charge-history — the store's charge history (UI-SPEC §6.6). Reuses jx-data-table.
 *
 * Money/dates/ids are mono; status is TEXT + COLOR (never color-only — a11y). Empty
 * state is actionable ("Nenhuma cobrança ainda…"). The "Faturas de taxas" section of
 * wireframe 16 is OUT of this phase — the page renders a disabled "Disponível em breve"
 * placeholder (Phase 11), never fake data. Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-charge-history',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent],
  template: `
    <jx-data-table
      caption="Histórico de cobranças"
      [columns]="columns"
      [rows]="rows()"
      [state]="state()"
      emptyTitle="Nenhuma cobrança ainda"
      emptyMessage="Sua primeira cobrança aparece após ativar um plano."
    >
      <ng-template #row let-item>
        <td class="jx-charge-history__mono">{{ item.date }}</td>
        <td>{{ item.description }}</td>
        <td class="jx-charge-history__mono jx-charge-history__num">{{ item.amount }}</td>
        <td>
          <span
            class="jx-charge-history__status"
            [style.color]="'var(' + item.statusColor + ')'"
          >
            {{ item.status }}
          </span>
        </td>
      </ng-template>
    </jx-data-table>
  `,
  styleUrl: './jx-charge-history.component.scss',
})
export class ChargeHistoryComponent {
  private readonly _charges = signal<ChargeHistoryItem[]>([]);
  private readonly _state = signal<DataTableState>('ready');

  @Input()
  set charges(v: ChargeHistoryItem[]) {
    this._charges.set(v ?? []);
    this._state.set((v ?? []).length === 0 ? 'empty' : 'ready');
  }
  @Input()
  set loading(v: boolean) {
    if (v) this._state.set('loading');
  }

  protected readonly state = this._state;

  protected readonly columns: DataTableColumn[] = [
    { key: 'date', label: 'Data' },
    { key: 'description', label: 'Descrição' },
    { key: 'amount', label: 'Valor', numeric: true },
    { key: 'status', label: 'Status' },
  ];

  protected readonly rows = computed<ChargeRow[]>(() =>
    this._charges().map((c) => {
      const meta = STATUS_META[c.status] ?? { label: c.status, cssVar: '--text-muted' };
      const displayDate = c.due_at ?? c.created_at;
      return {
        date: displayDate ? new Date(displayDate).toLocaleDateString('pt-BR') : '—',
        description: c.kind === 'subscription' ? 'Assinatura' : 'Entrega',
        amount: formatCents(c.amount_cents),
        status: meta.label,
        statusColor: meta.cssVar,
      };
    }),
  );
}
