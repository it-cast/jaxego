import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

/** Plan shape from GET /v1/plans (values from the SEED — DRV-009). */
export interface Plan {
  codename: string;
  nome: string;
  preco_cents: number;
  entregas_mes: number;
  taxa_entrega_cents: number;
  is_free: boolean;
  is_unlimited: boolean;
}

/**
 * jx-plan-card — a subscription plan card (UI-SPEC §6.1). DATA-DRIVEN: every
 * value (price, deliveries, fee) comes from the `plan` input (GET /v1/plans);
 * NO plan value is hardcoded here (DRV-009). Price in mono (ui-ux-pro-max).
 *
 * Anti-dark-pattern (UI-SPEC §6.2): the "Continuar no Free" CTA carries the same
 * visual weight as the paid CTA. Tokens: only semantic vars (no hex).
 */
@Component({
  selector: 'jx-plan-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article
      class="jx-plan"
      [class.jx-plan--current]="selected"
      [attr.aria-label]="'Plano ' + plan.nome"
    >
      @if (selected) {
        <span class="jx-plan__pill">Seu plano</span>
      }
      <h3 class="jx-plan__name">{{ plan.nome }}</h3>
      <b class="jx-plan__price">{{ priceLabel }}</b>
      <small class="jx-plan__details">{{ detailsLabel }}</small>
      <button
        type="button"
        class="jx-plan__cta"
        [class.jx-plan__cta--fill]="plan.is_free"
        (click)="choose.emit(plan)"
      >
        {{ ctaLabel }}
      </button>
    </article>
  `,
  styleUrl: './plan-card.component.scss',
})
export class PlanCardComponent {
  @Input({ required: true }) plan!: Plan;
  @Input() selected = false;
  @Output() choose = new EventEmitter<Plan>();

  protected get priceLabel(): string {
    if (this.plan.preco_cents === 0) {
      return 'R$ 0';
    }
    return this.formatBrl(this.plan.preco_cents);
  }

  protected get detailsLabel(): string {
    const entregas = this.plan.is_unlimited
      ? 'ilimitado'
      : `${this.plan.entregas_mes} entregas/mês`;
    return `${entregas} · taxa ${this.formatBrl(this.plan.taxa_entrega_cents)}/entrega`;
  }

  protected get ctaLabel(): string {
    return this.plan.is_free
      ? 'Continuar no Free'
      : `Escolher ${this.plan.nome}`;
  }

  private formatBrl(cents: number): string {
    return (cents / 100).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  }
}
