import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import {
  MerchantStatusBanner,
  OnboardingHintComponent,
} from './dashboard/onboarding-hint.component';

/**
 * Loja dashboard — post-activation onboarding (UI-SPEC §7). Shows the
 * pending_payment/pending_validation banner (E3/E4) above the first-delivery
 * hint, driven by the `status` query param set after signup. The hint is
 * progressive disclosure (dismissible), never a blocking tour.
 */
@Component({
  selector: 'jx-loja-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [OnboardingHintComponent],
  template: `
    <main class="jx-loja-inicio">
      <jx-onboarding-hint [status]="status()" />
    </main>
  `,
  styles: [
    `
      .jx-loja-inicio {
        max-width: 720px;
        margin: var(--jx-space-6) auto;
        padding: 0 var(--jx-space-4);
      }
    `,
  ],
})
export class LojaInicioPage {
  private readonly route = inject(ActivatedRoute);
  protected readonly status = signal<MerchantStatusBanner>(this.readStatus());

  private readStatus(): MerchantStatusBanner {
    const raw = this.route.snapshot.queryParamMap.get('status');
    return raw === 'pending_payment' || raw === 'pending_validation' ? raw : null;
  }
}
