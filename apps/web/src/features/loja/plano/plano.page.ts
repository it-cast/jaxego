import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { LoadingSkeletonComponent } from '@jaxego/shared/state';
import { PlanCardComponent, type Plan } from '@jaxego/shared/components';
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
  ],
  template: `
    <main class="jx-plano">
      <header class="jx-plano__header">
        <h1 class="jx-h1">Seu <em>plano.</em></h1>
        <p class="jx-plano__lead">Escolha o que faz sentido para a sua loja. Mude quando quiser.</p>
      </header>

      @if (subscription(); as sub) {
        <jx-subscription-status
          class="jx-plano__status"
          [status]="sub.billing_status"
          [amountCents]="sub.amount_cents"
          [nextDueAt]="sub.next_due_at"
          [planName]="currentPlanName()"
        />
      }

      @if (plans().length === 0) {
        <jx-loading-skeleton variant="block" height="56px" />
      } @else {
        <button type="button" class="jx-plano__change-btn" (click)="openPlanModal()">
          Alterar plano
        </button>
      }

      <section class="jx-plano__history" aria-label="Histórico de cobranças">
        <h2 class="jx-h2">Cobranças</h2>
        <jx-charge-history [charges]="charges()" />
      </section>

      <section class="jx-plano__invoices" aria-label="Faturas de taxas">
        <h2 class="jx-h2">Faturas de taxas</h2>
        <p class="jx-plano__placeholder">Disponível em breve.</p>
      </section>
    </main>

    <!-- Modal: seleção de plano -->
    @if (showPlanModal()) {
      <div class="jx-modal-overlay" (click)="closePlanModal()" role="dialog" aria-modal="true" aria-label="Alterar plano">
        <div class="jx-modal" (click)="$event.stopPropagation()">
          <div class="jx-modal__header">
            <h2 class="jx-modal__title">Alterar plano</h2>
            <button type="button" class="jx-modal__close" aria-label="Fechar" (click)="closePlanModal()">×</button>
          </div>
          <div class="jx-modal__body jx-plano__plan-grid">
            @for (plan of plans(); track plan.codename) {
              <jx-plan-card
                [plan]="plan"
                [selected]="plan.codename === current()"
                (choose)="onPlanSelected($event)"
              />
            }
          </div>
        </div>
      </div>
    }

    <!-- Modal: pagamento -->
    @if (showPaymentModal()) {
      <div class="jx-modal-overlay" role="dialog" aria-modal="true" aria-label="Pagamento">
        <div class="jx-modal jx-modal--narrow" (click)="$event.stopPropagation()">
          <div class="jx-modal__header">
            <h2 class="jx-modal__title">
              @if (pixConfirmed()) { Assinatura ativada! } @else { Pagamento }
            </h2>
            <button type="button" class="jx-modal__close" aria-label="Fechar" (click)="closePaymentModal()">×</button>
          </div>
          <div class="jx-modal__body">

            @if (pixConfirmed()) {
              <!-- Tela de sucesso PIX dentro do modal -->
              <div class="jx-plano__pix-success">
                <div class="jx-plano__pix-success-icon" aria-hidden="true">✓</div>
                <p class="jx-plano__pix-success-msg">PIX confirmado. Seu plano foi ativado.</p>
                <button type="button" class="jx-plano__pix-btn" (click)="closePaymentModal()">
                  Continuar
                </button>
              </div>

            } @else if (pixPending()) {
              <!-- QR exibido aguardando pagamento -->
              <div class="jx-plano__pix-result" role="status" aria-live="polite">
                @if (pixQrImage()) {
                  <img [src]="pixQrImage()!" alt="QR Code PIX" class="jx-plano__pix-qr" />
                }
                @if (pixQrCode()) {
                  <p class="jx-plano__pix-code">{{ pixQrCode() }}</p>
                  <button type="button" class="jx-plano__pix-copy" (click)="copyPixCode()">
                    {{ pixCopied() ? 'Copiado!' : 'Copiar código PIX' }}
                  </button>
                }
                <p class="jx-plano__pix-note">
                  Aguardando confirmação do pagamento…
                </p>
              </div>

            } @else {
              <!-- Seleção de método + formulários -->
              <jx-checkout-method-toggle
                [method]="method()"
                (methodChange)="onMethodChange($event)"
              />
              @if (method() === 'card') {
                <jx-card-form ctaLabel="Confirmar pagamento" (cardEncrypted)="onCardEncrypted($event)" />
              } @else if (method() === 'pix') {
                <p class="jx-plano__pix-hint">
                  Ao confirmar, você autoriza o débito automático mensal via PIX.
                </p>
                <button
                  type="button"
                  class="jx-plano__pix-btn"
                  [disabled]="pixLoading()"
                  (click)="onPixSubmit()"
                >
                  {{ pixLoading() ? 'Aguarde...' : 'Autorizar PIX Recorrente' }}
                </button>
              }
            }

          </div>
        </div>
      </div>
    }
  `,
  styleUrl: './plano.page.scss',
})
export class PlanoPage implements OnDestroy {
  private readonly merchants = inject(MerchantService);
  private readonly billing = inject(BillingService);


  protected readonly plans = signal<Plan[]>([]);
  protected readonly current = signal<string>('free');
  protected readonly subscription = signal<SubscriptionView | null>(null);
  protected readonly charges = signal<ChargeHistoryItem[]>([]);
  protected readonly method = signal<CheckoutMethod>(null);
  protected readonly showPlanModal = signal(false);
  protected readonly showPaymentModal = signal(false);
  protected readonly pixLoading = signal(false);
  protected readonly pixPending = signal(false);
  protected readonly pixConfirmed = signal(false);
  protected readonly pixQrImage = signal<string | null>(null);
  protected readonly pixQrCode = signal<string | null>(null);
  protected readonly pixCopied = signal(false);
  protected readonly currentPlanName = computed(() => {
    const plan = this.plans().find((p) => p.codename === this.current());
    return plan?.nome ?? null;
  });
  @ViewChild(CardFormComponent) private cardForm?: CardFormComponent;

  private pendingPlanId: number | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    void this.load();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  protected openPlanModal(): void {
    this.showPlanModal.set(true);
  }

  protected closePlanModal(): void {
    this.showPlanModal.set(false);
  }

  protected closePaymentModal(): void {
    this.stopPolling();
    this.showPaymentModal.set(false);
    this.pendingPlanId = null;
    this.pixLoading.set(false);
    this.pixPending.set(false);
    this.pixConfirmed.set(false);
    this.pixQrImage.set(null);
    this.pixQrCode.set(null);
    this.method.set(null);
  }

  protected onMethodChange(m: CheckoutMethod): void {
    this.method.set(m);
  }

  protected async onPixSubmit(): Promise<void> {
    const sub = this.subscription();
    if (!sub || this.pixLoading()) return;
    this.pixLoading.set(true);
    try {
      const result = await this.billing.subscribe({
        plan_id: this.pendingPlanId ?? sub.plan_id,
        cycle: 'mensal',
        method: 'pix',
        pix_recorrente: true,
      });
      this.pixQrImage.set(result.qr_code_base64 ?? null);
      this.pixQrCode.set(result.qr_code ?? null);
      this.pixPending.set(true);
      this.startPolling();
    } catch {
      // backend error — modal stays open so user can retry
    } finally {
      this.pixLoading.set(false);
    }
  }

  protected async copyPixCode(): Promise<void> {
    const code = this.pixQrCode();
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      this.pixCopied.set(true);
      setTimeout(() => this.pixCopied.set(false), 2000);
    } catch {
      // clipboard blocked — code visible for manual copy
    }
  }

  protected onPlanSelected(plan: Plan): void {
    this.closePlanModal();
    const planId = (plan as unknown as { id?: number }).id;
    if (plan.is_free) {
      void this.applyPlanChange(planId ?? null);
    } else {
      this.pendingPlanId = planId ?? null;
      this.showPaymentModal.set(true);
    }
  }

  protected async onCardEncrypted(blob: string): Promise<void> {
    const sub = this.subscription();
    if (!sub) return;
    try {
      const updated = await this.billing.subscribe({
        plan_id: this.pendingPlanId ?? sub.plan_id,
        cycle: 'mensal',
        method: 'card',
        card_blob: blob,
      });
      this.subscription.set(updated);
      this.updateCurrent(updated.plan_id);
      this.charges.set(await this.billing.charges());
      this.closePaymentModal();
    } catch {
      this.cardForm?.setState('recusado');
    }
  }

  private startPolling(): void {
    this.pollTimer = setInterval(() => void this.checkPixStatus(), 5000);
  }

  private stopPolling(): void {
    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private async checkPixStatus(): Promise<void> {
    try {
      const sub = await this.billing.subscription();
      if (sub.billing_status === 'active') {
        this.stopPolling();
        this.subscription.set(sub);
        this.updateCurrent(sub.plan_id);
        this.charges.set(await this.billing.charges());
        this.pixConfirmed.set(true);
      }
    } catch {
      // silently retry on next tick
    }
  }

  private async applyPlanChange(planId: number | null): Promise<void> {
    if (planId == null) return;
    try {
      await this.billing.changePlan(planId);
      const sub = await this.billing.subscription();
      this.subscription.set(sub);
      this.updateCurrent(sub.plan_id);
      this.charges.set(await this.billing.charges());
    } catch {
      // backend rejects invalid change; state unchanged
    }
  }

  private updateCurrent(planId: number): void {
    const match = this.plans().find((p) => (p as unknown as { id?: number }).id === planId);
    if (match) this.current.set(match.codename);
  }

  private async load(): Promise<void> {
    const plans = await this.merchants.listPlans();
    this.plans.set(plans);
    try {
      const sub = await this.billing.subscription();
      this.subscription.set(sub);
      const match = plans.find((p) => (p as unknown as { id?: number }).id === sub.plan_id);
      this.current.set(match?.codename ?? 'free');
      this.charges.set(await this.billing.charges());
    } catch {
      // no subscription yet
    }
  }
}
