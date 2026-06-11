import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { LoadingSkeletonComponent } from '../../../shared/state';
import { PlanCardComponent, type Plan } from '../../../shared/components';
import { MerchantService } from '../cadastro/merchant.service';
import {
  BillingService,
  type ChargeHistoryItem,
  type SubscriptionView,
} from './billing.service';
import { SubscriptionStatusComponent } from './components/jx-subscription-status.component';
import { ChargeHistoryComponent } from './components/jx-charge-history.component';

/**
 * Seleção de plano (tela 16, UI-SPEC §6) — plan management + subscription status +
 * charge history. Cards are data-driven by GET /v1/plans (SEED values — DRV-009,
 * zero hardcode). The subscription banner + history are Phase 10. The "Faturas de
 * taxas" wireframe section is OUT (Phase 11) — rendered as a disabled placeholder,
 * never fake data.
 */
@Component({
  selector: 'jx-plano',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    PlanCardComponent,
    LoadingSkeletonComponent,
    SubscriptionStatusComponent,
    ChargeHistoryComponent,
  ],
  template: `
    <main class="jx-plano">
      <header class="jx-plano__header">
        <h1 class="jx-h1">Seu <em>plano.</em></h1>
        <p class="jx-plano__lead">Escolha o que faz sentido para a sua loja. Mude quando quiser.</p>
      </header>

      @if (subscription(); as sub) {
        <jx-subscription-status
          [status]="sub.billing_status"
          [amountCents]="sub.amount_cents"
          [nextDueAt]="sub.next_due_at"
        />
      }

      <section class="jx-plano__grid" aria-label="Planos disponíveis">
        @for (plan of plans(); track plan.codename) {
          <jx-plan-card [plan]="plan" [selected]="plan.codename === current()" />
        } @empty {
          <jx-loading-skeleton variant="block" height="160px" />
        }
      </section>

      <section class="jx-plano__history" aria-label="Histórico de cobranças">
        <h2 class="jx-h2">Cobranças</h2>
        <jx-charge-history [charges]="charges()" />
      </section>

      <section class="jx-plano__invoices" aria-label="Faturas de taxas">
        <h2 class="jx-h2">Faturas de taxas</h2>
        <p class="jx-plano__placeholder">Disponível em breve.</p>
      </section>
    </main>
  `,
  styleUrl: './plano.page.scss',
})
export class PlanoPage {
  private readonly merchants = inject(MerchantService);
  private readonly billing = inject(BillingService);

  protected readonly plans = signal<Plan[]>([]);
  protected readonly current = signal<string>('free');
  protected readonly subscription = signal<SubscriptionView | null>(null);
  protected readonly charges = signal<ChargeHistoryItem[]>([]);

  constructor() {
    void this.load();
  }

  private async load(): Promise<void> {
    this.plans.set(await this.merchants.listPlans());
    try {
      this.subscription.set(await this.billing.subscription());
      this.charges.set(await this.billing.charges());
    } catch {
      // No subscription yet (trial pending) — the banner simply does not render.
    }
  }
}
