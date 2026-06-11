import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  signal,
} from '@angular/core';

export type CheckoutMethod = 'card' | 'pix';

/**
 * jx-checkout-method-toggle — choose card | PIX (UI-SPEC §6.1).
 *
 * Two large radios in a `role="radiogroup"`; the selected option gets the brand
 * wash. Above them, a security band (lock + "Pagamento criptografado · Safe2Pay")
 * — the icon is aria-hidden, the meaning is in the text (trust-safety-ux). Each
 * option is ≥44px. Disabled while processing (foco preso no painel ativo).
 * Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-checkout-method-toggle',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-method">
      <p class="jx-method__security">
        <span class="jx-method__lock" aria-hidden="true">🔒</span>
        Pagamento criptografado · Safe2Pay
      </p>
      <div class="jx-method__options" role="radiogroup" aria-label="Forma de pagamento">
        <button
          type="button"
          class="jx-method__option"
          role="radio"
          [attr.aria-checked]="value() === 'card'"
          [class.jx-method__option--on]="value() === 'card'"
          [disabled]="disabled"
          (click)="select('card')"
        >
          <span class="jx-method__title">Cartão de crédito</span>
          <span class="jx-method__sub">Cobrança recorrente automática</span>
        </button>
        <button
          type="button"
          class="jx-method__option"
          role="radio"
          [attr.aria-checked]="value() === 'pix'"
          [class.jx-method__option--on]="value() === 'pix'"
          [disabled]="disabled"
          (click)="select('pix')"
        >
          <span class="jx-method__title">PIX automático</span>
          <span class="jx-method__sub">Autorize uma vez, renova sozinho</span>
        </button>
      </div>
    </div>
  `,
  styleUrl: './jx-checkout-method-toggle.component.scss',
})
export class CheckoutMethodToggleComponent {
  protected readonly value = signal<CheckoutMethod>('card');
  @Input() disabled = false;

  @Input()
  set method(v: CheckoutMethod) {
    this.value.set(v);
  }

  @Output() methodChange = new EventEmitter<CheckoutMethod>();

  protected select(m: CheckoutMethod): void {
    if (this.disabled) return;
    this.value.set(m);
    this.methodChange.emit(m);
  }
}
