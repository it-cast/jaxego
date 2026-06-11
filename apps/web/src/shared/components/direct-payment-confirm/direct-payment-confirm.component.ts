import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

export type DirectPaymentOutcome = 'cash' | 'pix' | 'not_received';

/**
 * jx-direct-payment-confirm — "Recebeu o pagamento?" fieldset (RN-026 / D-05).
 *
 * A deliberate radio choice (NO swipe — gesture-touch: critical actions need a
 * deliberate tap). "Recebi" (cash/pix) confirms the amount; "Não recebi" concludes
 * the delivery (ENTREGUE) and opens a dispute server-side, WITHOUT punishing the
 * courier (trust-safety — the copy reassures). Buttons ≥52px. Tokens only — no hex.
 */
@Component({
  selector: 'jx-direct-payment-confirm',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <fieldset class="jx-dpc">
      <legend class="jx-dpc__legend">Recebeu o pagamento de {{ amountLabel }}?</legend>
      <div class="jx-dpc__options">
        <button
          type="button"
          class="jx-dpc__btn jx-dpc__btn--ok"
          (click)="confirm.emit('cash')"
        >
          Recebi em dinheiro
        </button>
        <button
          type="button"
          class="jx-dpc__btn jx-dpc__btn--ok"
          (click)="confirm.emit('pix')"
        >
          Recebi em PIX
        </button>
        <button
          type="button"
          class="jx-dpc__btn jx-dpc__btn--no"
          (click)="confirm.emit('not_received')"
        >
          Não recebi
        </button>
      </div>
      <p class="jx-dpc__hint">
        Se não recebeu, a entrega é concluída e abrimos uma análise — você não é
        penalizado por isso.
      </p>
    </fieldset>
  `,
  styleUrl: './direct-payment-confirm.component.scss',
})
export class DirectPaymentConfirmComponent {
  /** The amount to confirm, already formatted (e.g. "R$ 25,00"). */
  @Input() amountLabel = '';

  @Output() confirm = new EventEmitter<DirectPaymentOutcome>();
}
