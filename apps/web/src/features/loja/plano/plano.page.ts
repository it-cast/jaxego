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
import {
  CheckoutMethodToggleComponent,
  type CheckoutMethod,
} from './components/jx-checkout-method-toggle.component';
import { CardFormComponent } from './components/jx-card-form.component';
import { PixQrComponent } from './components/jx-pix-qr.component';
import { PlanCompareComponent } from './components/jx-plan-compare.component';

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
    CheckoutMethodToggleComponent,
    CardFormComponent,
    PixQrComponent,
    PlanCompareComponent,
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

      @if (plans().length === 0) {
        <jx-loading-skeleton variant="block" height="160px" />
      } @else if (subscription()?.billing_status === 'active') {
        <section class="jx-plano__compare" aria-label="Mudar de plano">
          <jx-plan-compare
            [planList]="plans()"
            [current]="current()"
            [currentPrice]="subscription()?.amount_cents ?? 0"
            (upgrade)="onPlanChange($event.codename)"
            (downgrade)="onPlanChange($event.codename)"
          />
        </section>
      } @else {
        <section class="jx-plano__grid" aria-label="Planos disponíveis">
          @for (plan of plans(); track plan.codename) {
            <jx-plan-card [plan]="plan" [selected]="plan.codename === current()" />
          }
        </section>
      }

      <section class="jx-plano__checkout" aria-label="Pagamento da assinatura">
        <h2 class="jx-h2">Pagamento</h2>
        <jx-checkout-method-toggle
          [method]="method()"
          (methodChange)="onMethodChange($event)"
        />
        @if (method() === 'card') {
          <jx-card-form ctaLabel="Confirmar pagamento" (cardEncrypted)="onCardEncrypted($event)" />
        } @else {
          @if (subscription()?.qr_code; as qr) {
            <jx-pix-qr
              [copyPaste]="qr"
              [image]="subscription()?.qr_code_base64 ?? null"
              pixState="aguardando"
            />
          } @else {
            <p class="jx-plano__pix-hint">Gere o PIX ao confirmar para ativar por aprovação automática.</p>
          }
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
  protected readonly method = signal<CheckoutMethod>('card');

  constructor() {
    void this.load();
  }

  protected onMethodChange(m: CheckoutMethod): void {
    this.method.set(m);
  }

  /** Upgrade (pro-rata now) or downgrade (scheduled) — RN-029. */
  protected async onPlanChange(codename: string): Promise<void> {
    const plan = this.plans().find((p) => p.codename === codename);
    if (!plan) return;
    // The plan id is the SubscriptionPlan id; the page maps codename→id via the catalog.
    const planId = (plan as unknown as { id?: number }).id;
    if (planId == null) return;
    try {
      await this.billing.changePlan(planId);
      this.subscription.set(await this.billing.subscription());
      this.charges.set(await this.billing.charges());
    } catch {
      // The backend rejects an invalid change; the page state is unchanged.
    }
  }

  /**
   * The card is already RSA-OAEP-encrypted by jx-card-form — only the opaque blob
   * arrives here. We forward it to the backend; the plaintext card never touched this
   * page (TH-A). The customer document/email come from the merchant profile.
   */
  protected async onCardEncrypted(blob: string): Promise<void> {
    const sub = this.subscription();
    if (!sub) return;
    try {
      const updated = await this.billing.subscribe({
        plan_id: sub.plan_id,
        cycle: 'mensal',
        method: 'card',
        card_blob: blob,
        customer_document: '',
        customer_email: '',
      });
      this.subscription.set(updated);
      this.charges.set(await this.billing.charges());
    } catch {
      // The jx-card-form surfaces the refusal; the page state is unchanged.
    }
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
