import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent, WarnBannerComponent } from '../../shared/state';

/**
 * Início do entregador (T-12). When the courier carries the mei_pending flag
 * (RN-024), a PERMANENT, non-dismissible jx-warn-banner explains that they may
 * work the direct-from-store flow and how to regularise — explicative, not
 * punitive (trust-safety). The flag is an input (driven by the courier profile
 * once that endpoint lands); the banner only renders when it is true.
 */
@Component({
  selector: 'jx-entregador-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent, WarnBannerComponent],
  template: `
    <ion-content>
      @if (meiPending) {
        <jx-warn-banner
          message="Você ainda não tem MEI ativo. Pode entregar recebendo direto da loja. Para receber pela plataforma, regularize seu MEI."
        />
      }
      <jx-empty-state
        icon="🛵"
        title="Tudo pronto pra rodar."
        message="As corridas da sua área aparecem aqui quando começarem."
      />
    </ion-content>
  `,
})
export class EntregadorInicioPage {
  /** RN-024: when true, the permanent regularisation banner is shown. */
  @Input() meiPending = false;
}
