import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEye } from '@fortawesome/free-solid-svg-icons';
import { StateBadgeComponent } from '../state-badge/state-badge.component';
import type { DeliveryListItem } from '../../models/delivery.models';
import { formatBrl } from '../../util/money';

/**
 * jx-delivery-row — the `<td>`s for one delivery row (UI-SPEC §4.1), projected
 * into `jx-data-table`. Nº/Date/Freight in mono; state via `jx-state-badge`
 * (variant `list`). The "Cancelar" action appears ONLY in CRIADA (pre-acceptance,
 * zero cost RN-004/D-03); other states show only "ver". The recipient phone is
 * NOT shown (LGPD — only name/neighborhood); if ever shown it is the masked value.
 * Tokens only — no hex.
 */
@Component({
  selector: 'jx-delivery-row',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [StateBadgeComponent, FaIconComponent],
  template: `
    <td class="jx-delivery-row__num">{{ shortToken }}</td>
    <td class="jx-delivery-row__date">{{ dateLabel }}</td>
    <td>{{ delivery.recipient_name || '—' }}</td>
    <td class="jx-delivery-row__freight">{{ freightLabel }}</td>
    <td>{{ paymentLabel }}</td>
    <td><jx-state-badge [state]="delivery.state" variant="list" /></td>
    <td class="jx-delivery-row__actions">
      @if (delivery.state === 'CRIADA') {
        <button
          type="button"
          class="jx-delivery-row__cancel"
          (click)="cancelDelivery.emit(delivery)"
        >
          Cancelar
        </button>
      }
      <button type="button" class="jx-delivery-row__view" (click)="view.emit(delivery)" aria-label="Ver entrega">
        <fa-icon [icon]="iconEye" aria-hidden="true" />
      </button>
    </td>
  `,
  styleUrl: './delivery-row.component.scss',
})
export class DeliveryRowComponent {
  protected readonly iconEye = faEye;
  @Input({ required: true }) delivery!: DeliveryListItem;
  @Output() cancelDelivery = new EventEmitter<DeliveryListItem>();
  @Output() view = new EventEmitter<DeliveryListItem>();

  protected get shortToken(): string {
    return '#' + this.delivery.public_token.slice(0, 6);
  }

  protected get dateLabel(): string {
    if (!this.delivery.created_at) {
      return '—';
    }
    const d = new Date(this.delivery.created_at);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  protected get freightLabel(): string {
    const price = this.delivery.price_cents;
    if (price === null || price === undefined) {
      return '—';
    }
    return formatBrl(price / 100);
  }

  protected get paymentLabel(): string {
    return { direct: 'Direto', pix: 'PIX', card: 'Cartão' }[this.delivery.payment_method];
  }
}
