import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { AuthService } from '../../core/auth/auth.service';
import { MoneyComponent, PaymentBadgeComponent } from '../../shared/components';
import { deliveryStateLabel, paymentMethodOf } from '../../shared/util/delivery-format';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '../../shared/state';
import { CourierDeliveryListItem, EntregadorService } from './entregador.service';

/**
 * Entregas do entregador (tela lista, F-06). Real history from
 * GET /v1/couriers/{id}/deliveries. No recipient PII in the list (server omits
 * it); tapping an in-progress one opens the active delivery. Tokens only.
 */
@Component({
  selector: 'jx-entregador-entregas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingSkeletonComponent,
    MoneyComponent,
    PaymentBadgeComponent,
  ],
  template: `
    <ion-content>
      <div class="jx-list">
        <h1 class="jx-list__title">Entregas</h1>
        @if (loading()) {
          <jx-loading-skeleton />
        } @else if (error()) {
          <jx-error-state
            message="Não foi possível carregar suas entregas."
            (retry)="reload()"
          />
        } @else if (!items().length) {
          <jx-empty-state
            icon="📦"
            title="Nenhuma corrida ainda."
            message="Quando você aceitar uma corrida, ela aparece aqui."
          />
        } @else {
          @for (d of items(); track d.id) {
            <article
              class="jx-list__row"
              [class.jx-list__row--active]="isActive(d.state)"
              [attr.role]="isActive(d.state) ? 'button' : null"
              [attr.tabindex]="isActive(d.state) ? 0 : null"
              (click)="open(d)"
              (keydown.enter)="open(d)"
              (keydown.space)="open(d)"
            >
              <div>
                <strong>{{ stateLabel(d.state) }}</strong>
                <p class="jx-list__muted">
                  <jx-payment-badge [method]="payOf(d.payment_method)" />
                  · {{ shortDate(d.created_at) }}
                </p>
              </div>
              <jx-money [cents]="d.estimate_min_cents ?? d.fee_cents" />
            </article>
          }
        }
      </div>
    </ion-content>
  `,
  styles: [
    `
      .jx-list {
        padding: var(--jx-space-4);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-2);
      }
      .jx-list__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0 0 var(--jx-space-2);
      }
      .jx-list__row {
        background: var(--jx-color-surface);
        border: 1px solid var(--jx-color-neutral-200);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .jx-list__row--active {
        border-color: var(--jx-color-brand-300);
        cursor: pointer;
      }
      .jx-list__muted {
        margin: 0;
        font-size: var(--jx-text-sm);
        color: var(--jx-color-neutral-500);
      }
    `,
  ],
})
export class EntregadorEntregasPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly router = inject(Router);

  protected readonly items = signal<CourierDeliveryListItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) {
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.error.set(false);
    try {
      const page = await this.svc.listDeliveries(id);
      this.items.set(page.items);
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected isActive(state: string): boolean {
    return state === 'ACEITA' || state === 'COLETADA';
  }

  protected open(d: CourierDeliveryListItem): void {
    if (this.isActive(d.state)) {
      void this.router.navigate(['/entregador/entrega-ativa']);
    }
  }

  protected readonly stateLabel = deliveryStateLabel;
  protected readonly payOf = paymentMethodOf;

  protected shortDate(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  }
}
