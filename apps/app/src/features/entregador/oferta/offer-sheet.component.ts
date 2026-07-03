import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  computed,
  signal,
} from '@angular/core';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStore, faLocationDot, faMoneyBill, faRoute } from '@fortawesome/free-solid-svg-icons';
import { WarnBannerComponent, ErrorStateComponent } from '@jaxego/shared/state';
import { formatBrl } from '@jaxego/shared/util/money';
import { OfferTimerComponent } from './offer-timer.component';
import type { OfferOut, OfferResult } from './offer.models';

/**
 * jx-offer-sheet — the offer bottom-sheet (tela 05, PEÇA CENTRAL — F-05/RN-013).
 * `role="dialog"` + focus trap; Esc does NOT close (the offer demands an explicit
 * decision — declining is the exit). Shows: store + cosmetic timer, pickup (full
 * address — store's own), destination (ONLY neighborhood + distance — RN-013,
 * NEVER street/number/recipient), the run value (mono brand), Accept/Decline, and
 * the terminal states (won / lost-the-race E3 / expired / network error).
 *
 * No swipe-to-accept (gesture-touch: an accidental accept costs the race); Accept
 * is a deliberate ~52px button. Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-offer-sheet',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [OfferTimerComponent, WarnBannerComponent, ErrorStateComponent, FaIconComponent],
  template: `
    @if (offerData(); as o) {
    <div class="jx-offer-overlay" role="presentation">
    <div
      class="jx-offer-sheet"
      role="dialog"
      aria-modal="true"
      [attr.aria-labelledby]="'offer-store-' + o.delivery_id"
    >
        <header class="jx-offer-sheet__head">
          <div>
            <p class="jx-offer-sheet__overline">NOVA OFERTA</p>
            <h2 class="jx-offer-sheet__store" [id]="'offer-store-' + o.delivery_id">
              {{ o.loja_nome }}
            </h2>
          </div>
          <jx-offer-timer [ttlTotalS]="o.ttl_total_s" [ttlRemainingS]="o.ttl_remaining_s" />
        </header>

        @if (resultState() === null) {
          <div class="jx-offer-sheet__stops">
            <div class="jx-stop jx-stop--pickup">
              <div class="jx-stop__icon-row">
                <fa-icon [icon]="iconStore" class="jx-stop__fa" aria-hidden="true" />
                <span class="jx-stop__overline">COLETA</span>
              </div>
              <span class="jx-stop__line">{{ o.pickup_address }}</span>
            </div>
            <div class="jx-stop jx-stop--dropoff">
              <div class="jx-stop__icon-row">
                <fa-icon [icon]="iconLocation" class="jx-stop__fa" aria-hidden="true" />
                <span class="jx-stop__overline">ENTREGA</span>
              </div>
              <span class="jx-stop__line">
                {{ o.dropoff_address }}@if (o.dropoff_number) {, {{ o.dropoff_number }}}@if (o.dropoff_neighborhood) {, {{ o.dropoff_neighborhood }}}
              </span>
              <span class="jx-stop__hint">{{ distanceKm() }}</span>
            </div>
          </div>

          <div class="jx-offer-sheet__value-card">
            <fa-icon [icon]="iconMoney" class="jx-offer-sheet__value-icon" aria-hidden="true" />
            <div class="jx-offer-sheet__value-info">
              <span class="jx-offer-sheet__value-label">Voce ganha</span>
              <span class="jx-offer-sheet__value-amount">{{ value() }}</span>
            </div>
          </div>

          <p class="jx-offer-sheet__receipt-text">
            <fa-icon [icon]="iconRoute" class="jx-offer-sheet__receipt-icon" aria-hidden="true" />
            Forma de recebimento do cliente: <strong>{{ receiptText() }}</strong>
          </p>

          <div class="jx-offer-sheet__actions">
            <button
              type="button"
              class="jx-offer-sheet__accept"
              [attr.aria-busy]="isProcessing()"
              [disabled]="isProcessing()"
              (click)="onAccept()"
            >
              {{ isProcessing() ? 'Aceitando…' : 'Aceitar entrega' }}
            </button>
            <button
              type="button"
              class="jx-offer-sheet__decline"
              [disabled]="isProcessing()"
              (click)="onDecline()"
            >
              Recusar
            </button>
          </div>
        } @else if (resultState() === 'won') {
          <div class="jx-offer-sheet__terminal" role="status">
            <p class="jx-offer-sheet__won">Entrega aceita! Vá até a coleta.</p>
          </div>
        } @else if (resultState() === 'lost') {
          <jx-warn-banner
            message="Essa entrega acabou de ser aceita por outro entregador. Sem problema — a próxima é sua."
          />
        } @else if (resultState() === 'expired') {
          <jx-warn-banner
            message="Essa oferta expirou. Já estamos buscando a próxima pra você."
          />
        } @else if (resultState() === 'error') {
          <jx-error-state
            message="Não deu pra confirmar agora."
            retryLabel="Tentar de novo"
            (retry)="onAccept()"
          />
        }
    </div>
    </div>
    }
  `,
  styleUrl: './offer-sheet.component.scss',
})
export class OfferSheetComponent {
  private readonly _offer = signal<OfferOut | null>(null);
  private readonly _result = signal<OfferResult | null>(null);
  private readonly _processing = signal(false);

  /** The active offer (RN-013 — no full destination address). */
  @Input() set offer(value: OfferOut | null) {
    this._offer.set(value);
  }

  /** The terminal result (won/lost/expired/error) — null while deciding. */
  @Input() set result(value: OfferResult | null) {
    this._result.set(value);
  }

  /** True while the accept is in flight (the lock decides on the server). */
  @Input() set processing(value: boolean) {
    this._processing.set(value);
  }

  @Output() accept = new EventEmitter<number>();
  @Output() decline = new EventEmitter<number>();

  protected readonly iconStore = faStore;
  protected readonly iconLocation = faLocationDot;
  protected readonly iconMoney = faMoneyBill;
  protected readonly iconRoute = faRoute;

  protected readonly offerData = computed(() => this._offer());
  protected readonly resultState = computed(() => this._result());
  protected readonly isProcessing = computed(() => this._processing());

  protected readonly value = computed(() => {
    const cents = this._offer()?.value_cents ?? null;
    return cents === null ? '—' : formatBrl(cents / 100);
  });

  protected readonly receiptText = computed(() => {
    const map: Record<string, string> = {
      dinheiro: 'Dinheiro',
      maquina_loja: 'Maquina da loja',
      aplicativo: 'Aplicativo',
      ja_pago: 'Ja pago',
    };
    const method = this._offer()?.receipt_method;
    return method ? (map[method] ?? 'Direto') : 'Direto';
  });

  protected readonly distanceKm = computed(() => {
    const m = this._offer()?.distance_m ?? null;
    if (m === null) return '~';
    const km = (m / 1000).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return `~${km} km`;
  });

  protected onAccept(): void {
    const id = this._offer()?.delivery_id;
    if (id != null) this.accept.emit(id);
  }

  protected onDecline(): void {
    const id = this._offer()?.delivery_id;
    if (id != null) this.decline.emit(id);
  }
}
