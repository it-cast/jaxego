import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { LoadingSkeletonComponent } from '../../../shared/state';
import { PlanCardComponent, type Plan } from '../../../shared/components';
import { MerchantService } from '../cadastro/merchant.service';

/**
 * Seleção de plano (tela 16, UI-SPEC §6) — standalone plan management screen.
 * Cards are data-driven by GET /v1/plans (SEED values — DRV-009, zero hardcode).
 * No dark pattern: "Continuar no Free" has the same weight as upgrade. The
 * invoices table from wireframe 16 is deferred to Phase 10 (out of scope here).
 */
@Component({
  selector: 'jx-plano',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PlanCardComponent, LoadingSkeletonComponent],
  template: `
    <main class="jx-plano">
      <header class="jx-plano__header">
        <h1 class="jx-h1">Seu <em>plano.</em></h1>
        <p class="jx-plano__lead">Escolha o que faz sentido para a sua loja. Mude quando quiser.</p>
      </header>

      <section class="jx-plano__grid" aria-label="Planos disponíveis">
        @for (plan of plans(); track plan.codename) {
          <jx-plan-card [plan]="plan" [selected]="plan.codename === current()" />
        } @empty {
          <jx-loading-skeleton variant="block" height="160px" />
        }
      </section>
    </main>
  `,
  styleUrl: './plano.page.scss',
})
export class PlanoPage {
  private readonly merchants = inject(MerchantService);

  protected readonly plans = signal<Plan[]>([]);
  protected readonly current = signal<string>('free');

  constructor() {
    void this.load();
  }

  private async load(): Promise<void> {
    this.plans.set(await this.merchants.listPlans());
  }
}
