import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faCheck, faStore, faLocationDot } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { MoneyComponent, PageHeaderComponent } from '@jaxego/shared/components';
import { CourierDelivery, EntregadorService } from '../entregador.service';

@Component({
  selector: 'jx-entregador-concluida',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, MoneyComponent, FaIconComponent, PageHeaderComponent],
  template: `
    <ion-content>
      <jx-page-header title="Entrega concluida" />
      <div class="jx-done">
        <div class="jx-done__check">
          <fa-icon [icon]="iconCheck" aria-hidden="true" />
        </div>
        <h1 class="jx-done__title">
          Entrega <span class="jx-done__accent">concluída!</span>
        </h1>

        @if (delivery(); as d) {
          <p class="jx-done__sub">{{ stateLabel(d.state) }}</p>

          <section class="jx-done__card">
            <div class="jx-done__card-row">
              <fa-icon [icon]="iconStore" class="jx-done__card-icon" aria-hidden="true" />
              <span class="jx-done__card-label">Coleta</span>
            </div>
            @if (d.merchant_trade_name) {
              <strong>{{ d.merchant_trade_name }}</strong>
            }
            <p class="jx-done__muted">{{ d.pickup_address }}</p>
          </section>

          <section class="jx-done__card">
            <div class="jx-done__card-row">
              <fa-icon [icon]="iconLocation" class="jx-done__card-icon jx-done__card-icon--dest" aria-hidden="true" />
              <span class="jx-done__card-label">Entrega</span>
            </div>
            @if (d.dropoff_address) {
              <strong>{{ d.dropoff_address }}@if (d.dropoff_number) {, {{ d.dropoff_number }}}</strong>
            }
            @if (d.recipient_name) {
              <p class="jx-done__muted">{{ d.recipient_name }}</p>
            }
          </section>

          <section class="jx-done__summary">
            <div class="jx-done__summary-row">
              <span>Valor da corrida</span>
              <jx-money [cents]="d.price_cents ?? d.fee_cents" />
            </div>
            @if (d.receipt_method) {
              <div class="jx-done__summary-row">
                <span>Recebimento do cliente</span>
                <strong>{{ receiptLabel(d.receipt_method) }}</strong>
              </div>
            }
            @if (d.courier_collection_method) {
              <div class="jx-done__summary-row">
                <span>Cobranca do entregador</span>
                <strong>{{ collectionLabel(d.courier_collection_method) }}</strong>
              </div>
            }
          </section>
        }

        <button type="button" class="jx-done__primary" (click)="goHome()">
          Voltar ao inicio
        </button>
      </div>
    </ion-content>
  `,
  styles: [`
    .jx-done {
      padding: var(--jx-space-5) var(--jx-space-4);
      display: flex; flex-direction: column; align-items: center;
      gap: var(--jx-space-3); text-align: center;
    }
    .jx-done__check {
      width: 72px; height: 72px; border-radius: 50%;
      background: var(--brand-wash, hsl(24 80% 95%));
      color: var(--brand, #e8722a);
      display: grid; place-items: center; font-size: 32px;
    }
    .jx-done__title {
      font-family: var(--jx-font-display);
      font-size: var(--jx-text-2xl); margin: 0;
    }
    .jx-done__accent {
      font-family: var(--jx-font-serif-accent);
      font-style: italic; color: var(--brand, #e8722a);
    }
    .jx-done__sub {
      margin: 0; color: var(--text-muted, #888); font-size: var(--jx-text-sm);
    }

    /* Cards */
    .jx-done__card {
      width: 100%; text-align: left;
      display: flex; flex-direction: column; gap: var(--jx-space-1);
      border-bottom: 1px solid var(--border, #eee);
      padding-bottom: var(--jx-space-3);
    }
    .jx-done__card-row {
      display: flex; align-items: center; gap: var(--jx-space-2);
    }
    .jx-done__card-icon {
      font-size: 16px; color: var(--brand, #e8722a);
    }
    .jx-done__card-icon--dest {
      color: hsl(0 70% 55%);
    }
    .jx-done__card-label {
      font-size: var(--jx-text-xs); font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.06em;
      color: var(--text-muted, #888);
    }
    .jx-done__muted {
      margin: 0; font-size: var(--jx-text-sm); color: var(--text-muted, #888);
    }

    /* Summary */
    .jx-done__summary {
      width: 100%; text-align: left;
      display: flex; flex-direction: column; gap: var(--jx-space-2);
      background: #fff; border: 1px solid var(--border, #eee);
      border-radius: 12px; padding: var(--jx-space-3);
    }
    .jx-done__summary-row {
      display: flex; align-items: center; justify-content: space-between;
      font-size: var(--jx-text-sm); color: var(--text-muted, #888);
    }
    .jx-done__summary-row strong { color: var(--text); }

    /* CTA */
    .jx-done__primary {
      width: 100%; min-height: 50px; margin-top: var(--jx-space-2);
      border: 0; border-radius: 999px;
      background: var(--brand, #e8722a); color: #fff;
      font-size: var(--jx-text-md); font-weight: 700; cursor: pointer;
    }
  `],
})
export class EntregadorConcluidaPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly router = inject(Router);

  protected readonly iconCheck = faCheck;
  protected readonly iconStore = faStore;
  protected readonly iconLocation = faLocationDot;

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

  protected receiptLabel(method: string): string {
    const map: Record<string, string> = {
      dinheiro: 'Dinheiro',
      maquina_loja: 'Máquina da loja',
      aplicativo: 'Aplicativo',
      ja_pago: 'Já pago',
    };
    return map[method] ?? method;
  }

  protected collectionLabel(method: string): string {
    return method === 'pix_app' ? 'PIX' : 'Em mãos';
  }

  protected goHome(): void {
    void this.router.navigate(['/entregador/inicio']);
  }
}
