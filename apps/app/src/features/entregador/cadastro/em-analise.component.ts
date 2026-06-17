import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent, WarnBannerComponent } from '@jaxego/shared/state';

/**
 * "Em análise" — post-submit surface (UI-SPEC §6.1, T-12). An informative
 * empty-state (role="status") — NO festivity/confetti. When the courier finished
 * with no active MEI, the permanent mei_pending banner (RN-024) explains the
 * direct-payment restriction without punishing tone. Zero hardcoded hex.
 */
@Component({
  selector: 'jx-entregador-em-analise',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent, WarnBannerComponent],
  template: `
    <ion-content class="jx-analise">
      @if (meiPending) {
        <jx-warn-banner
          message="Você ainda não tem MEI ativo. Pode entregar recebendo direto da loja. Para receber pela plataforma, regularize seu MEI."
        />
      }
      <jx-empty-state
        icon="◷"
        title="Recebemos seu cadastro."
        message="Estamos conferindo seus dados. Avisamos assim que liberar — costuma sair rápido."
      />
    </ion-content>
  `,
  styles: [
    `
      .jx-analise {
        --background: var(--surface);
      }
    `,
  ],
})
export class EntregadorEmAnalisePage {
  private readonly route = inject(ActivatedRoute);

  protected get meiPending(): boolean {
    return this.route.snapshot.queryParamMap.get('mei_pending') === '1';
  }
}
