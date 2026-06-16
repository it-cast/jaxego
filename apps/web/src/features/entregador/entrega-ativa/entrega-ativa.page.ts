import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { AuthService } from '../../../core/auth/auth.service';
import { LiveMapComponent } from '../../../shared/components/live-map/live-map.component';
import { PaymentBadgeComponent, type PaymentMethod } from '../../../shared/components';
import { EmptyStateComponent, ErrorStateComponent } from '../../../shared/state';
import { CourierDelivery, EntregadorService } from '../entregador.service';

/**
 * Entrega ativa (tela 05/tpl-c-active, F-06). The in-progress delivery the
 * courier is executing. States advance via PROOFS (RN-005), so the primary CTA
 * routes to the proof capture page:
 *   ACEITA   → "Coletei" → comprovar/pickup
 *   COLETADA → "Cheguei no destino" → comprovar/delivery (recusa → /refusal)
 * Destination address/recipient appear only AFTER pickup (RN-013) — the backend
 * already omits them pre-COLETADA, so we render what we get.
 */
@Component({
  selector: 'jx-entregador-entrega-ativa',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    EmptyStateComponent,
    ErrorStateComponent,
    LiveMapComponent,
    PaymentBadgeComponent,
  ],
  template: `
    <ion-content>
      @if (loading()) {
        <div class="jx-active__skeleton" aria-busy="true">Carregando…</div>
      } @else if (error()) {
        <jx-error-state
          message="Não foi possível carregar sua entrega agora."
          (retry)="reload()"
        />
      } @else if (!delivery()) {
        <jx-empty-state
          icon="🛵"
          title="Nenhuma entrega ativa"
          message="Quando você aceitar uma oferta, ela aparece aqui."
        />
      } @else {
        <div class="jx-active">
          @if (mapLat() !== null && mapLng() !== null) {
            <jx-live-map
              [lat]="mapLat()"
              [lng]="mapLng()"
              [ariaLabel]="mapAria()"
            />
          }

          <div class="jx-active__head">
            <div class="jx-active__staterow">
              <span class="jx-active__state">{{ stateLabel() }}</span>
              <jx-payment-badge [method]="payMethod()" />
            </div>
            <span class="jx-active__step">{{ stepLabel() }}</span>
          </div>

          <section class="jx-active__card">
            <span class="jx-active__eyebrow">Coleta</span>
            <strong>{{ delivery()!.pickup_address }}</strong>
            @if (delivery()!.pickup_neighborhood) {
              <p class="jx-active__muted">{{ delivery()!.pickup_neighborhood }}</p>
            }
          </section>

          <section class="jx-active__card jx-active__card--dest">
            <span class="jx-active__eyebrow">Entrega</span>
            @if (delivery()!.dropoff_address) {
              <strong>
                {{ delivery()!.dropoff_address }}@if (delivery()!.dropoff_number) {,
                  {{ delivery()!.dropoff_number }}}
              </strong>
              @if (delivery()!.recipient_name) {
                <p class="jx-active__muted">
                  {{ delivery()!.recipient_name }} ·
                  {{ delivery()!.recipient_phone_masked }}
                </p>
              }
            } @else {
              <strong>Bairro de destino</strong>
              <p class="jx-active__muted">
                Endereço exato liberado após a coleta.
              </p>
            }
          </section>

          <ol class="jx-active__tl">
            @for (s of steps(); track s.key) {
              <li
                [class.jx-active__tl--done]="s.done"
                [class.jx-active__tl--cur]="s.current"
              >
                {{ s.label }}
              </li>
            }
          </ol>

          <button
            type="button"
            class="jx-active__primary"
            (click)="advance()"
          >
            {{ primaryLabel() }}
          </button>

          @if (delivery()!.state === 'COLETADA') {
            <button
              type="button"
              class="jx-active__secondary"
              (click)="refusal()"
            >
              Destinatário ausente / recusou
            </button>
          }
        </div>
      }
    </ion-content>
  `,
  styles: [
    `
      .jx-active {
        padding: var(--jx-space-4);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-active__skeleton {
        padding: var(--jx-space-6);
        text-align: center;
        color: var(--jx-color-neutral-500);
      }
      .jx-active__head {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-active__staterow {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
      }
      .jx-active__state {
        font-family: var(--jx-font-mono);
        font-size: var(--jx-text-xs);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--jx-color-brand-600);
        font-weight: 700;
      }
      .jx-active__step {
        font-size: var(--jx-text-sm);
        color: var(--jx-color-neutral-600);
      }
      .jx-active__card {
        background: var(--jx-color-surface);
        border: 1px solid var(--jx-color-neutral-200);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-active__card--dest {
        border-color: var(--jx-color-brand-100);
        background: var(--jx-color-brand-50);
      }
      .jx-active__eyebrow {
        font-family: var(--jx-font-mono);
        font-size: var(--jx-text-xs);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--jx-color-neutral-500);
      }
      .jx-active__muted {
        margin: 0;
        font-size: var(--jx-text-sm);
        color: var(--jx-color-neutral-500);
      }
      .jx-active__tl {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-active__tl li {
        font-size: var(--jx-text-sm);
        color: var(--jx-color-neutral-500);
        padding-left: var(--jx-space-3);
        position: relative;
      }
      .jx-active__tl li::before {
        content: '○';
        position: absolute;
        left: 0;
      }
      .jx-active__tl--done {
        color: var(--jx-color-neutral-800);
      }
      .jx-active__tl--done::before {
        content: '●';
        color: var(--jx-color-semantic-success);
      }
      .jx-active__tl--cur {
        color: var(--jx-color-neutral-900);
        font-weight: 700;
      }
      .jx-active__tl--cur::before {
        content: '●';
        color: var(--jx-color-brand-500);
      }
      .jx-active__primary,
      .jx-active__secondary {
        border: 0;
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-3);
        font-size: var(--jx-text-base);
        font-weight: 700;
        cursor: pointer;
        min-height: 48px;
      }
      .jx-active__primary {
        background: var(--jx-color-neutral-800);
        color: var(--jx-neutral-50);
      }
      .jx-active__secondary {
        background: transparent;
        color: var(--jx-color-semantic-error);
        border: 1px solid var(--jx-color-neutral-300);
      }
    `,
  ],
})
export class EntregadorEntregaAtivaPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly router = inject(Router);

  protected readonly delivery = signal<CourierDelivery | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);

  /** Map focuses the destination after pickup (COLETADA), else the pickup point. */
  protected readonly mapLat = computed<number | null>(() => {
    const d = this.delivery();
    if (!d) return null;
    return d.state === 'COLETADA' && d.dropoff_lat != null ? d.dropoff_lat : d.pickup_lat;
  });
  protected readonly mapLng = computed<number | null>(() => {
    const d = this.delivery();
    if (!d) return null;
    return d.state === 'COLETADA' && d.dropoff_lng != null ? d.dropoff_lng : d.pickup_lng;
  });

  protected payMethod(): PaymentMethod {
    const m = this.delivery()?.payment_method;
    return m === 'pix' || m === 'card' ? m : 'direct';
  }

  protected mapAria(): string {
    return this.delivery()?.state === 'COLETADA'
      ? 'Mapa do destino da entrega'
      : 'Mapa do ponto de coleta';
  }

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    const courierId = this.auth.me()?.courier_id;
    if (!courierId) {
      this.loading.set(false);
      this.delivery.set(null);
      return;
    }
    this.loading.set(true);
    this.error.set(false);
    try {
      this.delivery.set(await this.svc.activeDelivery(courierId));
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected stateLabel(): string {
    const map: Record<string, string> = {
      ACEITA: 'Aceita',
      COLETADA: 'Coletada',
    };
    return map[this.delivery()?.state ?? ''] ?? this.delivery()?.state ?? '';
  }

  protected stepLabel(): string {
    return this.delivery()?.state === 'COLETADA'
      ? 'A caminho do destino'
      : 'Indo coletar';
  }

  protected primaryLabel(): string {
    return this.delivery()?.state === 'COLETADA'
      ? 'Cheguei no destino — comprovar'
      : 'Coletei — tirar foto';
  }

  protected steps(): { key: string; label: string; done: boolean; current: boolean }[] {
    const state = this.delivery()?.state;
    const collected = state === 'COLETADA';
    return [
      { key: 'aceita', label: 'Aceita', done: true, current: false },
      { key: 'coleta', label: 'Coletar e fotografar', done: collected, current: !collected },
      { key: 'entrega', label: 'Entregar no destino', done: false, current: collected },
      { key: 'comprovar', label: 'Comprovar entrega', done: false, current: false },
    ];
  }

  protected advance(): void {
    const d = this.delivery();
    if (!d) return;
    const kind = d.state === 'COLETADA' ? 'delivery' : 'pickup';
    void this.router.navigate(['/entregador/entrega', d.id, 'comprovar', kind]);
  }

  protected refusal(): void {
    const d = this.delivery();
    if (!d) return;
    void this.router.navigate(['/entregador/entrega', d.id, 'comprovar', 'refusal']);
  }
}
