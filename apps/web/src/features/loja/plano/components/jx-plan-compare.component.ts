import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  computed,
  signal,
} from '@angular/core';
import { PlanCardComponent, type Plan } from '@jaxego/shared/components';
import { formatCents } from '../billing.service';

/**
 * jx-plan-compare — upgrade/downgrade comparison (UI-SPEC §6.5 / RN-029).
 *
 * Reuses jx-plan-card in a grid; the current plan is marked selected. A more expensive
 * plan → "Fazer upgrade (cobrança pro-rata hoje)"; a cheaper plan → "Mudar no próximo
 * ciclo". Choosing opens a confirmation panel (role=dialog) with the EXACT pro-rata value
 * (mono) or the scheduled date. Anti-dark-pattern (payment-checkout-ux): no countdown, no
 * "última chance", "Cancelar" of equal weight, downgrade never hidden. Tokens only — no hex.
 */
@Component({
  selector: 'jx-plan-compare',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PlanCardComponent],
  template: `
    <div class="jx-plan-compare">
      <div class="jx-plan-compare__grid">
        @for (plan of plans(); track plan.codename) {
          <div class="jx-plan-compare__cell">
            <jx-plan-card [plan]="plan" [selected]="plan.codename === currentCodename()" />
            @if (plan.codename !== currentCodename()) {
              <button
                type="button"
                class="jx-plan-compare__cta"
                (click)="choose(plan)"
              >
                {{ plan.preco_cents > currentPriceCents() ? 'Fazer upgrade' : 'Mudar no próximo ciclo' }}
              </button>
            }
          </div>
        }
      </div>

      @if (pending(); as p) {
        <div class="jx-plan-compare__confirm" role="dialog" aria-modal="true" aria-label="Confirmar mudança de plano">
          @if (p.preco_cents > currentPriceCents()) {
            <p>
              Você paga <strong class="jx-plan-compare__mono">{{ prorataLabel() }}</strong> agora
              pelos dias restantes deste ciclo e muda para o {{ p.nome }} na hora.
            </p>
            <div class="jx-plan-compare__actions">
              <button type="button" class="jx-plan-compare__confirm-btn" (click)="confirm(p)">
                Confirmar upgrade
              </button>
              <button type="button" class="jx-plan-compare__cancel" (click)="cancel()">Cancelar</button>
            </div>
          } @else {
            <p>
              Seu plano muda para {{ p.nome }} no fim do ciclo atual. Até lá os limites atuais
              continuam.
            </p>
            <div class="jx-plan-compare__actions">
              <button type="button" class="jx-plan-compare__confirm-btn" (click)="confirm(p)">
                Agendar mudança
              </button>
              <button type="button" class="jx-plan-compare__cancel" (click)="cancel()">Cancelar</button>
            </div>
          }
        </div>
      }
    </div>
  `,
  styleUrl: './jx-plan-compare.component.scss',
})
export class PlanCompareComponent {
  protected readonly plans = signal<Plan[]>([]);
  protected readonly currentCodename = signal<string>('free');
  protected readonly currentPriceCents = signal(0);
  protected readonly prorataCents = signal(0);
  protected readonly pending = signal<Plan | null>(null);

  @Input()
  set planList(v: Plan[]) {
    this.plans.set(v ?? []);
  }
  @Input()
  set current(codename: string) {
    this.currentCodename.set(codename);
  }
  @Input()
  set currentPrice(cents: number) {
    this.currentPriceCents.set(cents);
  }
  @Input()
  set prorata(cents: number) {
    this.prorataCents.set(cents);
  }

  @Output() upgrade = new EventEmitter<Plan>();
  @Output() downgrade = new EventEmitter<Plan>();

  protected readonly prorataLabel = computed(() => formatCents(this.prorataCents()));

  protected choose(plan: Plan): void {
    this.pending.set(plan);
  }

  protected cancel(): void {
    this.pending.set(null);
  }

  protected confirm(plan: Plan): void {
    if (plan.preco_cents > this.currentPriceCents()) this.upgrade.emit(plan);
    else this.downgrade.emit(plan);
    this.pending.set(null);
  }
}
