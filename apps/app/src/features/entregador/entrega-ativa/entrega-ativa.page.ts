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
import { AuthService } from '@jaxego/core/auth/auth.service';
import { LiveMapComponent } from '@jaxego/shared/components/live-map/live-map.component';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStore, faLocationDot, faBoxOpen, faNoteSticky, faHandHoldingDollar, faMobileScreen } from '@fortawesome/free-solid-svg-icons';
import { PageHeaderComponent, PaymentBadgeComponent, type PaymentMethod } from '@jaxego/shared/components';
import {
  deliveryStateLabel,
  packageLabel as fmtPackage,
  paymentMethodOf,
} from '@jaxego/shared/util/delivery-format';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '@jaxego/shared/state';
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
    LoadingSkeletonComponent,
    LiveMapComponent,
    PaymentBadgeComponent,
    FaIconComponent,
    PageHeaderComponent,
  ],
  template: `
    <ion-content>
      @if (loading()) {
        <div class="jx-active" aria-busy="true"><jx-loading-skeleton /></div>
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
        <jx-page-header title="Entrega ativa" backLink="/entregador/inicio" />
        <div class="jx-active">
          @if (mapLat() !== null && mapLng() !== null) {
            <jx-live-map
              [lat]="mapLat()"
              [lng]="mapLng()"
              [ariaLabel]="mapAria()"
            />
          }

          <section class="jx-active__card">
            <div class="jx-active__card-row">
              <fa-icon [icon]="iconStore" class="jx-active__card-icon" aria-hidden="true" />
              <span class="jx-active__eyebrow">Coleta</span>
            </div>
            @if (delivery()!.merchant_trade_name) {
              <strong class="jx-active__store-name">{{ delivery()!.merchant_trade_name }}</strong>
            }
            <p class="jx-active__muted">{{ delivery()!.pickup_address }}</p>
            @if (delivery()!.pickup_neighborhood) {
              <p class="jx-active__muted">{{ delivery()!.pickup_neighborhood }}</p>
            }
            @if (delivery()!.items_description) {
              <div class="jx-active__info-line">
                <fa-icon [icon]="iconBox" class="jx-active__info-icon" aria-hidden="true" />
                <span>{{ delivery()!.items_description }} (x{{ delivery()!.items_quantity }})</span>
              </div>
            }
            @if (packageLabel()) {
              <div class="jx-active__info-line">
                <fa-icon [icon]="iconBox" class="jx-active__info-icon" aria-hidden="true" />
                <span>{{ packageLabel() }}</span>
              </div>
            }
            @if (delivery()!.notes) {
              <div class="jx-active__info-line jx-active__info-line--notes">
                <fa-icon [icon]="iconNotes" class="jx-active__info-icon" aria-hidden="true" />
                <span>{{ delivery()!.notes }}</span>
              </div>
            }
          </section>

          <section class="jx-active__card jx-active__card--dest">
            <div class="jx-active__card-row">
              <fa-icon [icon]="iconLocation" class="jx-active__card-icon jx-active__card-icon--dest" aria-hidden="true" />
              <span class="jx-active__eyebrow">Entrega</span>
            </div>
            @if (delivery()!.dropoff_address) {
              <strong>
                {{ delivery()!.dropoff_address }}@if (delivery()!.dropoff_number) {, {{ delivery()!.dropoff_number }}}
              </strong>
              @if (delivery()!.recipient_name) {
                <p class="jx-active__muted">{{ delivery()!.recipient_name }}</p>
              }
            } @else {
              <strong>Bairro de destino</strong>
              <p class="jx-active__muted">Endereco exato liberado apos a coleta.</p>
            }
          </section>

          @if (delivery()!.receipt_method || delivery()!.courier_collection_method) {
            <div class="jx-active__payment-info">
              @if (delivery()!.receipt_method) {
                <p class="jx-active__receipt-line">
                  Forma de recebimento do cliente: <strong>{{ receiptLabel() }}</strong>
                </p>
              }
              @if (delivery()!.courier_collection_method) {
                <p class="jx-active__receipt-line">
                  Forma de cobranca do entregador: <strong>{{ collectionLabel() }}</strong>
                </p>
              }
            </div>
          }

          @if (delivery()!.state === 'COLETADA' && !delivery()!.courier_collection_method) {
            <button type="button" class="jx-active__primary" (click)="showCollectionModal.set(true)">
              Cobrar entrega
            </button>
          } @else {
            <button type="button" class="jx-active__primary" (click)="advance()">
              {{ primaryLabel() }}
            </button>
          }

          @if (delivery()!.courier_collection_method && delivery()!.state === 'COLETADA') {
            <button type="button" class="jx-active__secondary" (click)="refusal()">
              Destinatario ausente / recusou
            </button>
          }

          @if (showCollectionModal()) {
            <div class="jx-active__overlay" (click)="showCollectionModal.set(false)">
              <div class="jx-active__modal" (click)="$event.stopPropagation()">
                <h2 class="jx-active__modal-title">Como vai cobrar?</h2>
                <button type="button" class="jx-active__modal-opt" (click)="setCollection('in_hand')">
                  <fa-icon [icon]="iconHand" class="jx-active__modal-fa" aria-hidden="true" />
                  <span class="jx-active__modal-label">Recebi em maos</span>
                  <span class="jx-active__modal-desc">Dinheiro ou PIX direto para voce</span>
                </button>
                <button type="button" class="jx-active__modal-opt" (click)="setCollection('pix_app')">
                  <fa-icon [icon]="iconMobile" class="jx-active__modal-fa" aria-hidden="true" />
                  <span class="jx-active__modal-label">Cobrar com PIX</span>
                  <span class="jx-active__modal-desc">Gerar QR Code para o destinatario pagar</span>
                </button>
                <button type="button" class="jx-active__modal-cancel" (click)="showCollectionModal.set(false)">
                  Cancelar
                </button>
              </div>
            </div>
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
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-active__card + .jx-active__card {
        margin-top: 2em;
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
      .jx-active__notes {
        margin: 0;
        font-size: var(--jx-text-sm);
        color: var(--jx-color-brand-600);
        font-weight: 600;
        font-style: italic;
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
      .jx-active__store-name {
        font-size: var(--jx-text-md); color: var(--text);
      }
      .jx-active__card-row {
        display: flex; align-items: center; gap: var(--jx-space-2);
      }
      .jx-active__card-icon {
        font-size: 18px; color: var(--brand, #e8722a); margin-top: 2px; flex-shrink: 0;
      }
      .jx-active__card-icon--dest {
        color: var(--jx-color-brand-600, #c2410c);
      }
      .jx-active__info-line {
        display: flex; align-items: center; gap: var(--jx-space-2);
        font-size: var(--jx-text-sm); color: var(--text-muted, #888);
        padding-left: 26px;
      }
      .jx-active__info-line--notes {
        color: var(--brand, #e8722a); font-weight: 600; font-style: italic;
      }
      .jx-active__info-icon {
        font-size: 14px; color: var(--text-muted, #888); flex-shrink: 0;
      }
      .jx-active__info-line--notes .jx-active__info-icon {
        color: var(--brand, #e8722a);
      }
      .jx-active__payment-info {
        display: flex; flex-direction: column; gap: var(--jx-space-1);
        margin-bottom: 2em;
      }
      .jx-active__receipt-line {
        margin: 0; font-size: var(--jx-text-sm); color: var(--text-muted, #888);
      }
      .jx-active__receipt-line strong { color: var(--text); }
      .jx-active__primary {
        background: var(--brand, #e8722a);
        color: #fff;
        border-radius: 999px;
      }
      .jx-active__secondary {
        background: transparent;
        color: var(--brand, #e8722a);
        border: 2px solid var(--brand, #e8722a);
        border-radius: 999px;
      }
      .jx-active__overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0);
        display: flex;
        align-items: flex-end;
        justify-content: center;
        z-index: 100;
        animation: jx-fade-in 0.25s ease forwards;
      }
      @keyframes jx-fade-in {
        to { background: rgba(0,0,0,0.5); }
      }
      .jx-active__modal {
        width: 100%;
        max-width: 420px;
        background: var(--jx-color-surface, #fff);
        border-radius: 20px 20px 0 0;
        padding: var(--jx-space-5);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
        animation: jx-slide-up 0.3s cubic-bezier(0.22, 1, 0.36, 1) forwards;
      }
      @keyframes jx-slide-up {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
      }
      .jx-active__modal-title {
        margin: 0;
        font-size: var(--jx-text-lg);
        font-weight: 700;
        text-align: center;
      }
      .jx-active__modal-opt {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--jx-space-1);
        padding: var(--jx-space-4);
        background: #fff;
        border: 2px solid #e8722a69;
        border-radius: var(--jx-radius-lg);
        cursor: pointer;
        font: inherit;
        text-align: center;
      }
      .jx-active__modal-opt:hover {
        background: var(--brand-wash, hsl(24 80% 95%));
      }
      .jx-active__modal-fa {
        font-size: 24px; color: var(--brand, #e8722a);
      }
      .jx-active__modal-label {
        font-weight: 700;
        font-size: var(--jx-text-md);
      }
      .jx-active__modal-desc {
        font-size: var(--jx-text-xs);
        color: var(--jx-color-neutral-500);
      }
      .jx-active__modal-cancel {
        border: 0;
        background: transparent;
        color: var(--jx-color-neutral-500);
        font: inherit;
        font-size: var(--jx-text-sm);
        cursor: pointer;
        padding: var(--jx-space-2);
        text-align: center;
      }
    `,
  ],
})
export class EntregadorEntregaAtivaPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly router = inject(Router);

  protected readonly iconStore = faStore;
  protected readonly iconLocation = faLocationDot;
  protected readonly iconBox = faBoxOpen;
  protected readonly iconNotes = faNoteSticky;
  protected readonly iconHand = faHandHoldingDollar;
  protected readonly iconMobile = faMobileScreen;

  protected readonly delivery = signal<CourierDelivery | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly showCollectionModal = signal(false);

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

  protected packageLabel(): string {
    return fmtPackage(this.delivery() ?? {});
  }

  protected payMethod(): PaymentMethod {
    return paymentMethodOf(this.delivery()?.payment_method);
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
    return deliveryStateLabel(this.delivery()?.state);
  }

  protected stepLabel(): string {
    return this.delivery()?.state === 'COLETADA'
      ? 'A caminho do destino'
      : 'Indo coletar';
  }

  protected primaryLabel(): string {
    return this.delivery()?.state === 'COLETADA'
      ? 'Cheguei no destino'
      : 'Coletei';
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

  protected receiptLabel(): string {
    const map: Record<string, string> = {
      dinheiro: '💵 Dinheiro',
      maquina_loja: '💳 Máquina da loja',
      aplicativo: '📱 Aplicativo',
    };
    return map[this.delivery()?.receipt_method ?? ''] ?? '';
  }

  protected collectionLabel(): string {
    const m = this.delivery()?.courier_collection_method;
    return m === 'pix_app' ? '📱 Cobrança via PIX' : '💵 Recebido em mãos';
  }

  protected async setCollection(method: 'in_hand' | 'pix_app'): Promise<void> {
    const d = this.delivery();
    const courierId = this.auth.me()?.courier_id;
    if (!d || !courierId) return;
    try {
      await this.svc.setCollectionMethod(courierId, d.id, method);
      this.showCollectionModal.set(false);
      await this.reload();
    } catch {
      // stay on modal
    }
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
