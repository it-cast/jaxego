import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

export type PaymentMethod = 'direct' | 'pix' | 'card';

/**
 * jx-payment-badge — selo do método de pagamento da corrida (assinatura visual
 * do protótipo). "Direto" usa o amarelo `--jx-payment-direct` (dinheiro/PIX na
 * mão); PIX/cartão usam o azul informativo (plataforma). Texto + ícone, nunca cor
 * sozinha (accessibility-pro). Tokens only.
 */
@Component({
  selector: 'jx-payment-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="jx-pay" [class.jx-pay--direct]="method === 'direct'">
      @if (method === 'direct') {
        <span aria-hidden="true">💵</span> Direto
      } @else if (method === 'pix') {
        PIX
      } @else {
        Cartão
      }
    </span>
  `,
  styles: [
    `
      .jx-pay {
        display: inline-block;
        font-size: var(--jx-text-2xs, 11px);
        font-weight: var(--jx-weight-bold);
        padding: 2px 9px;
        border-radius: var(--jx-radius-full);
        background: var(--jx-info-bg);
        color: var(--jx-info);
        white-space: nowrap;
      }
      .jx-pay--direct {
        background: var(--jx-payment-direct);
        color: var(--jx-payment-direct-ink);
      }
    `,
  ],
})
export class PaymentBadgeComponent {
  @Input({ required: true }) method: PaymentMethod = 'direct';
}
