import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  computed,
  signal,
} from '@angular/core';
import { MoneyComponent } from '../money/money.component';

/** Invoice status from GET /v1/invoices (mirrors `INVOICE_STATUSES` — backend). */
export type InvoiceStatus = 'open' | 'overdue' | 'paid';

/** The fields jx-invoice-summary needs (subset of InvoiceRow — invoices.router). */
export interface InvoiceSummary {
  id: number;
  /** Billed month as `YYYY-MM` (the backend `competence`). */
  competence: string;
  amount_cents: number;
  status: InvoiceStatus;
  /** ISO due date. */
  due_at: string;
  /** ISO paid date (when status === 'paid'). */
  paid_at?: string | null;
}

interface StatusMeta {
  /** Semantic colour var (text + border over a neutral surface — dark-mode pattern). */
  tone: 'success' | 'warning' | 'error';
  icon: string;
  label: string;
}

const MONTHS = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
];

/**
 * jx-invoice-summary — the store's monthly platform-fee invoice card (UI-SPEC §15).
 *
 * Shows the competence ("Fatura de maio de 2026"), the total in MONO via jx-money,
 * the due date, a status badge (em aberto / vencida / paga) and the "Pagar" CTA.
 * Status is NEVER colour-only — the badge carries text + icon + colour (a11y). The
 * value never recomputes layout (CLS): it is formatted client-side once. The CTA is
 * suppressed for a paid invoice. Tokens only — no hex (Gate 2).
 *
 * Copy (br/ux-copywriting-ptbr / UI-SPEC §copy): "Fatura de {competência} — vence em
 * {data}.". A `paying` flag drives the busy/disabled state of the CTA (the actual
 * checkout flow is owned by the host screen — payment-checkout-ux).
 */
@Component({
  selector: 'jx-invoice-summary',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MoneyComponent],
  template: `
    <article class="jx-inv" [attr.aria-label]="'Fatura de ' + competenceLabel()">
      <header class="jx-inv__head">
        <div class="jx-inv__title">
          <span class="jx-inv__overline">Fatura de</span>
          <h3 class="jx-inv__competence">{{ competenceLabel() }}</h3>
        </div>
        <span
          class="jx-inv__badge"
          [class.jx-inv__badge--success]="meta().tone === 'success'"
          [class.jx-inv__badge--warning]="meta().tone === 'warning'"
          [class.jx-inv__badge--error]="meta().tone === 'error'"
        >
          <span class="jx-inv__badge-icon" aria-hidden="true">{{ meta().icon }}</span>
          {{ meta().label }}
        </span>
      </header>

      <jx-money
        class="jx-inv__total"
        variant="display"
        [cents]="invoice.amount_cents"
        [label]="'Total da fatura'"
      />

      <p class="jx-inv__due">{{ dueLabel() }}</p>

      @if (invoice.status !== 'paid') {
        <button
          type="button"
          class="jx-inv__cta"
          [disabled]="paying"
          [attr.aria-busy]="paying"
          (click)="pay.emit(invoice.id)"
        >
          {{ paying ? 'Processando…' : 'Pagar fatura' }}
        </button>
      }
    </article>
  `,
  styleUrl: './invoice-summary.component.scss',
})
export class InvoiceSummaryComponent {
  private readonly _invoice = signal<InvoiceSummary | null>(null);

  @Input({ required: true })
  set invoice(value: InvoiceSummary) {
    this._invoice.set(value);
  }
  get invoice(): InvoiceSummary {
    return this._invoice()!;
  }

  /** Busy state for the CTA while the host runs the checkout flow. */
  @Input() paying = false;

  /** Emits the invoice id to pay (the host owns the checkout flow). */
  @Output() pay = new EventEmitter<number>();

  protected readonly META: Record<InvoiceStatus, StatusMeta> = {
    open: { tone: 'warning', icon: '◷', label: 'Em aberto' },
    overdue: { tone: 'error', icon: '!', label: 'Vencida' },
    paid: { tone: 'success', icon: '✓', label: 'Paga' },
  };

  protected readonly meta = computed(() => this.META[this._invoice()?.status ?? 'open']);

  protected competenceLabel(): string {
    const competence = this._invoice()?.competence ?? '';
    const [year, month] = competence.split('-').map((p) => parseInt(p, 10));
    if (!year || !month || month < 1 || month > 12) {
      return competence;
    }
    return `${MONTHS[month - 1]} de ${year}`;
  }

  protected dueLabel(): string {
    const inv = this._invoice();
    if (!inv) {
      return '';
    }
    if (inv.status === 'paid' && inv.paid_at) {
      return `Paga em ${this.formatDate(inv.paid_at)}.`;
    }
    return `Vence em ${this.formatDate(inv.due_at)}.`;
  }

  private formatDate(iso: string): string {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
      return iso;
    }
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  }
}
