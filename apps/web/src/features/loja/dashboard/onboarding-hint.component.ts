import {
  ChangeDetectionStrategy,
  Component,
  Input,
  signal,
} from '@angular/core';
import { WarnBannerComponent } from '../../../shared/state';

export type MerchantStatusBanner =
  | 'pending_payment'
  | 'pending_validation'
  | null;

/**
 * Onboarding hint + pending_* banners (UI-SPEC §4.3/§4.4/§7).
 *
 * Order (accessibility-pro): the status banner (E3/E4) renders ABOVE the
 * first-delivery hint. The hint is progressive disclosure, dismissible — never a
 * blocking modal/tour (onboarding-patterns). No festivity (ui-ux-pro-max). Tokens
 * are inherited semantic vars (dark mode via DEC-001); zero hardcoded hex.
 */
@Component({
  selector: 'jx-onboarding-hint',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [WarnBannerComponent],
  template: `
    <div class="jx-onboarding">
      @if (status === 'pending_payment') {
        <jx-warn-banner
          [message]="
            'Seu pagamento do plano ' +
            (planName || 'escolhido') +
            ' ainda não foi concluído. Você está usando o Free por enquanto.'
          "
        />
      } @else if (status === 'pending_validation') {
        <jx-warn-banner
          message="Estamos confirmando seu CNPJ na Receita. Sua loja já funciona no plano Free enquanto isso."
        />
      }

      @if (!dismissed()) {
        <section class="jx-onboarding__hint" aria-label="Primeiros passos">
          <h2 class="jx-onboarding__title">Tudo pronto. Bora a <em>primeira</em> entrega?</h2>
          <p class="jx-onboarding__text">
            Crie sua primeira entrega e acompanhe em tempo real.
          </p>
          <div class="jx-onboarding__actions">
            <a class="jx-onboarding__cta" href="/loja/nova-entrega">Criar entrega</a>
            <button
              type="button"
              class="jx-onboarding__dismiss"
              (click)="dismissed.set(true)"
            >
              Agora não
            </button>
          </div>
        </section>
      }
    </div>
  `,
  styleUrl: './onboarding-hint.component.scss',
})
export class OnboardingHintComponent {
  @Input() status: MerchantStatusBanner = null;
  @Input() planName?: string;

  protected readonly dismissed = signal(false);
}
