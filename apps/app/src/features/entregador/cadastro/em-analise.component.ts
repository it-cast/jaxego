import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
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
  imports: [RouterLink, EmptyStateComponent, WarnBannerComponent],
  template: `
    <div class="jx-analise">
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
      <a routerLink="/entrar" class="jx-analise__btn">Voltar ao login</a>
    </div>
  `,
  styles: [
    `
      .jx-analise {
        background: var(--surface);
        height: 100vh;
        height: 100dvh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--jx-space-4);
        gap: var(--jx-space-4);
      }
      .jx-analise__btn {
        display: inline-block;
        min-height: 48px;
        line-height: 48px;
        padding: 0 var(--jx-space-5);
        background: var(--brand);
        color: var(--brand-contrast, #fff);
        border-radius: var(--jx-radius-md);
        font-weight: var(--jx-weight-semibold);
        text-decoration: none;
        text-align: center;
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
