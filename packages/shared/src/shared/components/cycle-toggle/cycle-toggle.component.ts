import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

export type BillingCycle = 'mensal' | 'anual';

/**
 * jx-cycle-toggle — toggle Mensal / Anual para seleção de planos.
 * Emite `cycleChange` ao trocar. Badge "2 meses grátis" no anual.
 */
@Component({
  selector: 'jx-cycle-toggle',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-cycle" role="group" aria-label="Ciclo de cobrança">
      <button
        type="button"
        class="jx-cycle__btn"
        [class.jx-cycle__btn--active]="cycle === 'mensal'"
        [attr.aria-pressed]="cycle === 'mensal'"
        (click)="select('mensal')"
      >
        Mensal
      </button>
      <button
        type="button"
        class="jx-cycle__btn"
        [class.jx-cycle__btn--active]="cycle === 'anual'"
        [attr.aria-pressed]="cycle === 'anual'"
        (click)="select('anual')"
      >
        Anual
        <span class="jx-cycle__badge">2 meses grátis</span>
      </button>
    </div>
  `,
  styles: [`
    .jx-cycle {
      display: inline-flex;
      border: 1px solid var(--brand);
      border-radius: 8px;
      overflow: hidden;
      background: var(--surface-elevated, #f3f4f6);
    }
    .jx-cycle__btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 20px;
      font-size: 0.875rem;
      font-weight: 500;
      border: none;
      background: transparent;
      cursor: pointer;
      color: var(--text-muted);
      transition: background 0.15s, color 0.15s;
    }
    .jx-cycle__btn--active {
      background: var(--brand);
      color: var(--brand-contrast, #fff);
      border-radius: 6px;
    }
    .jx-cycle__badge {
      font-size: 0.7rem;
      font-weight: 600;
      background: var(--success, #16a34a);
      color: #fff;
      border-radius: 999px;
      padding: 1px 7px;
    }
    .jx-cycle__btn--active .jx-cycle__badge {
      background: rgba(255,255,255,0.25);
    }
  `],
})
export class CycleToggleComponent {
  @Input() cycle: BillingCycle = 'mensal';
  @Output() cycleChange = new EventEmitter<BillingCycle>();

  select(c: BillingCycle): void {
    if (c !== this.cycle) {
      this.cycleChange.emit(c);
    }
  }
}
