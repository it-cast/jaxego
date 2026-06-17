import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';
import { formatCents } from '../../util/money';

/** Visual weight of the value (UI-SPEC §Tokens): normal inline vs. large highlight. */
export type MoneyVariant = 'inline' | 'display';

/** Sign treatment for ledger rows: credit (+) / debit (−) / plain. */
export type MoneySign = 'none' | 'credit' | 'debit';

/**
 * jx-money — the SINGLE governed way to render a monetary value (UI-SPEC §Tokens).
 *
 * Money crosses the API as INTEGER cents (DRV-009); this component formats
 * cents→reais pt-BR (`R$ 0,00`) ONLY at the display edge, reusing the central
 * `formatCents` helper (shared/util/money) — the same masking lineage as the
 * Phase 4/7 currency inputs, never duplicated. The value renders in the MONO
 * family (ui-ux-pro-max: numbers in a tabular monospace align and read as money).
 *
 * a11y: the formatted string IS the accessible text; an optional `[label]` is
 * exposed via `aria-label` so a value in a dense table still announces its meaning
 * (e.g. "Saldo disponível R$ 120,00"). Status is NEVER carried by colour alone —
 * `sign` adds a textual +/− glyph, and the credit/debit colour is reinforcement.
 * Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-money',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-money"
      [class.jx-money--display]="variant === 'display'"
      [class.jx-money--credit]="sign === 'credit'"
      [class.jx-money--debit]="sign === 'debit'"
      [attr.aria-label]="ariaLabel()"
    >
      @if (sign !== 'none') {
        <span class="jx-money__sign" aria-hidden="true">{{ signGlyph() }}</span>
      }
      <span class="jx-money__value">{{ formatted() }}</span>
    </span>
  `,
  styleUrl: './money.component.scss',
})
export class MoneyComponent {
  private readonly _cents = signal(0);

  /** The amount in INTEGER cents (DRV-009). */
  @Input({ required: true })
  set cents(value: number) {
    this._cents.set(value ?? 0);
  }
  get cents(): number {
    return this._cents();
  }

  /** Visual weight: `inline` (default) or `display` (large highlight, e.g. balance). */
  @Input() variant: MoneyVariant = 'inline';

  /** Sign treatment for ledger rows (credit/debit) — adds a +/− glyph + colour. */
  @Input() sign: MoneySign = 'none';

  /** Optional descriptive label exposed via aria-label (e.g. "Saldo disponível"). */
  @Input() label?: string;

  protected readonly formatted = computed(() => formatCents(this._cents()));

  protected signGlyph(): string {
    return this.sign === 'credit' ? '+' : this.sign === 'debit' ? '−' : '';
  }

  protected ariaLabel(): string | null {
    const value = this.formatted();
    const signed =
      this.sign === 'credit'
        ? `mais ${value}`
        : this.sign === 'debit'
          ? `menos ${value}`
          : value;
    return this.label ? `${this.label}: ${signed}` : null;
  }
}
