import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent, WarnBannerComponent } from '../../shared/state';
import { AvailabilityToggleComponent } from './disponibilidade/availability-toggle.component';

/** The 4 mutually-exclusive dispatch states on the home (UI-SPEC §2.3). */
export type DispatchHomeState = 'offline' | 'waiting' | 'offer-active' | 'busy';

/**
 * Início do entregador (tela 04, F-05). Header with the reused
 * jx-availability-toggle (Phase 6) + the 4 mutually-exclusive dispatch states
 * (UI-SPEC §2.3): offline / waiting for offers / offer active (the jx-offer-sheet
 * rises over the home — wired in T-11) / in a delivery (busy, read-only here).
 *
 * The courier only receives offers while ONLINE (D-01). The mei_pending banner
 * (RN-024) stays permanent when set. A discreet pulsing dot signals "waiting"
 * (motion.slow, reduced-motion → static). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-entregador-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent, WarnBannerComponent, AvailabilityToggleComponent],
  template: `
    <ion-content>
      <header class="jx-home-header">
        <div class="jx-home-greeting">
          <span class="jx-home-greeting__hi">Olá,</span>
          <span class="jx-home-greeting__name">{{ name }}</span>
        </div>
        <jx-availability-toggle
          [isOnline]="isOnline()"
          [disabled]="kycPending"
          (onlineChange)="setOnline($event)"
        />
      </header>

      @if (meiPending) {
        <jx-warn-banner
          message="Você ainda não tem MEI ativo. Pode entregar recebendo direto da loja. Para receber pela plataforma, regularize seu MEI."
        />
      }

      <div class="jx-home-dispatch">
        @switch (state()) {
          @case ('offline') {
            <jx-empty-state
              icon="🛵"
              title="Você está offline"
              message="Fique online para receber ofertas da sua área."
            />
          }
          @case ('waiting') {
            <div class="jx-home-waiting">
              <span class="jx-home-pulse" aria-hidden="true"></span>
              <jx-empty-state
                icon="📡"
                title="Aguardando ofertas"
                message="As corridas da sua área aparecem aqui assim que surgirem."
              />
            </div>
          }
          @case ('busy') {
            <div class="jx-home-busy" role="status">
              <p class="jx-home-busy__title">Você está em uma entrega</p>
              @if (busyNeighborhood) {
                <p class="jx-home-busy__where">Destino: {{ busyNeighborhood }}</p>
              }
            </div>
          }
          @case ('offer-active') {
            <!-- The jx-offer-sheet rises over the home (T-11). -->
            <jx-empty-state icon="🔔" title="Nova oferta" message="Abrindo oferta…" />
          }
        }
      </div>
    </ion-content>
  `,
  styleUrl: './inicio.page.scss',
})
export class EntregadorInicioPage {
  private readonly _online = signal(false);
  private readonly _offerActive = signal(false);
  private readonly _busy = signal(false);

  /** Courier display name. */
  @Input() name = '';
  /** RN-024: when true, the permanent regularisation banner is shown. */
  @Input() meiPending = false;
  /** KYC incomplete (Phase 5) → the toggle is disabled. */
  @Input() kycPending = false;
  /** Destination neighborhood while busy (read-only here; execution is Phase 9). */
  @Input() busyNeighborhood: string | null = null;

  @Input() set online(value: boolean) {
    this._online.set(value);
  }
  @Input() set offerActive(value: boolean) {
    this._offerActive.set(value);
  }
  @Input() set busy(value: boolean) {
    this._busy.set(value);
  }

  protected readonly isOnline = computed(() => this._online());

  /** The single active dispatch state (mutually exclusive — UI-SPEC §2.3). */
  protected readonly state = computed<DispatchHomeState>(() => {
    if (this._busy()) {
      return 'busy';
    }
    if (!this._online()) {
      return 'offline';
    }
    return this._offerActive() ? 'offer-active' : 'waiting';
  });

  protected setOnline(value: boolean): void {
    this._online.set(value);
  }
}
