import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { MoneyComponent } from '@jaxego/shared/components';
import { CourierDelivery, EntregadorService } from '../entregador.service';

/**
 * Entrega concluída (tela tpl-c-done, F-06). Success summary after the delivery
 * proof + payment confirmation: value received, platform fee, and a return CTA.
 * Reads the delivery (now ENTREGUE/RECUSADA) by id. Tokens only.
 */
@Component({
  selector: 'jx-entregador-concluida',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, MoneyComponent],
  template: `
    <ion-content>
      <div class="jx-done">
        <div class="jx-done__check" aria-hidden="true">✓</div>
        <h1 class="jx-done__title">
          Entrega <span class="jx-done__accent">concluída.</span>
        </h1>
        @if (delivery(); as d) {
          <p class="jx-done__sub">{{ stateLabel(d.state) }}</p>
          <section class="jx-done__card">
            <div class="jx-done__row">
              <span>{{ paymentLabel(d.payment_method) }}</span>
              <jx-money [cents]="d.estimate_min_cents ?? d.fee_cents" />
            </div>
            <div class="jx-done__row">
              <span>Taxa Jaxegô (na fatura da loja)</span>
              <jx-money [cents]="d.fee_cents" />
            </div>
          </section>
        }
        <button type="button" class="jx-done__primary" (click)="goHome()">
          Voltar ao início
        </button>
      </div>
    </ion-content>
  `,
  styles: [
    `
      .jx-done {
        padding: var(--jx-space-6) var(--jx-space-4);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--jx-space-3);
        text-align: center;
      }
      .jx-done__check {
        width: 72px;
        height: 72px;
        border-radius: var(--jx-radius-full);
        background: var(--jx-success-bg);
        color: var(--jx-color-semantic-success);
        display: grid;
        place-items: center;
        font-size: 36px;
      }
      .jx-done__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0;
      }
      .jx-done__accent {
        font-family: var(--jx-font-serif-accent);
        font-style: italic;
        color: var(--jx-color-brand-500);
      }
      .jx-done__sub {
        margin: 0;
        color: var(--jx-color-neutral-500);
        font-size: var(--jx-text-sm);
      }
      .jx-done__card {
        width: 100%;
        background: var(--jx-color-surface);
        border: 1px solid var(--jx-color-neutral-200);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-2);
        text-align: left;
      }
      .jx-done__row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: var(--jx-color-neutral-600);
        font-size: var(--jx-text-sm);
      }
      .jx-done__primary {
        width: 100%;
        border: 0;
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-3);
        background: var(--jx-color-brand-500);
        color: var(--jx-neutral-50);
        font-weight: 700;
        cursor: pointer;
        min-height: 48px;
      }
    `,
  ],
})
export class EntregadorConcluidaPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly router = inject(Router);

  protected readonly delivery = signal<CourierDelivery | null>(null);

  async ngOnInit(): Promise<void> {
    const id = Number(this.route.snapshot.paramMap.get('id') ?? 0);
    const courierId = this.auth.me()?.courier_id;
    if (!id || !courierId) return;
    try {
      this.delivery.set(await this.svc.getDelivery(courierId, id));
    } catch {
      this.delivery.set(null);
    }
  }

  protected stateLabel(state: string): string {
    const map: Record<string, string> = {
      ENTREGUE: 'Entregue ao destinatário',
      RECUSADA_NO_DESTINO: 'Recusada no destino',
      FINALIZADA: 'Finalizada',
    };
    return map[state] ?? state;
  }

  protected paymentLabel(method: string): string {
    const map: Record<string, string> = {
      direct: 'Recebido (pagamento direto)',
      pix: 'Pago via PIX (plataforma)',
      card: 'Pago no cartão (plataforma)',
    };
    return map[method] ?? method;
  }

  protected goHome(): void {
    void this.router.navigate(['/entregador/inicio']);
  }
}
