import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faChevronRight } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import {
  MoneyComponent,
} from '@jaxego/shared/components';
import { DotsLoaderComponent } from '@jaxego/shared/components';
import { WarnBannerComponent } from '@jaxego/shared/state';
import { Balance, SaldoService } from './saldo/saldo.service';
import { AvailabilityToggleComponent } from './disponibilidade/availability-toggle.component';
import { OfferMonitorService } from './oferta/offer-monitor.service';
import {
  CourierDelivery,
  CourierDeliveryListItem,
  CourierScore,
  EntregadorService,
} from './entregador.service';
import { deliveryStateLabel } from '@jaxego/shared/util/delivery-format';
import { CourierLocationService } from './courier-location.service';

/** Mutually-exclusive dispatch states on the home (UI-SPEC §2.3). */
type HomeState = 'offline' | 'waiting' | 'offer' | 'busy';

/**
 * Início do entregador (tela 04 / tpl-c-home, F-05). Smart component: loads the
 * courier's real saldo, score and recent deliveries, owns the online toggle
 * (PATCH availability) and the offer overlay (polls /offers/active; accept →
 * routes to the active delivery). The courier only receives offers while ONLINE
 * and idle (D-01). Tokens only — fidelity to the prototype.
 */
@Component({
  selector: 'jx-entregador-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    WarnBannerComponent,
    AvailabilityToggleComponent,
    MoneyComponent,
    DotsLoaderComponent,
    FaIconComponent,
  ],
  template: `
    <ion-content>
      @if (initialLoading()) {
        <jx-dots-loader />
      } @else {

      <!-- Header -->
      <header class="jx-home-header">
        <div class="jx-home-greeting">
          <span class="jx-home-greeting__hi">Olá {{ firstName() }}!</span>
          @if (online() && onlineUntil()) {
            <span class="jx-home-greeting__until">Online até {{ fmtOnlineUntil() }}</span>
          }
        </div>
        <jx-availability-toggle
          [isOnline]="online()"
          [disabled]="toggleDisabled()"
          disabledReason=""
          (onlineChange)="setOnline($event)"
          (seeValidation)="goProfile()"
        />
      </header>

      @if (showOnlineModal()) {
        <div class="jx-home-overlay" (click)="cancelOnline()">
          <div class="jx-home-modal" (click)="$event.stopPropagation()">
            <h2 class="jx-home-modal__title">Até quando quer ficar online?</h2>
            <input
              type="time"
              class="jx-home-modal__time"
              [value]="onlineUntilTime()"
              (change)="onlineUntilTime.set($any($event.target).value)"
            />
            <button type="button" class="jx-home-modal__confirm" (click)="confirmOnline()">
              Confirmar
            </button>
            <button type="button" class="jx-home-modal__cancel" (click)="cancelOnline()">
              Cancelar
            </button>
          </div>
        </div>
      }

      @if (kycPending()) {
        <div class="jx-home-warn-wrap">
          <div class="jx-home-kyc-card">
            <span class="jx-home-kyc-msg">Termine sua validação para ficar online e receber ofertas.</span>
            <button type="button" class="jx-home-kyc-btn" (click)="goDocumentacao()">Ver validação</button>
          </div>
        </div>
      }

      @if (meiPending()) {
        <jx-warn-banner
          message="Voce ainda nao tem MEI ativo. Pode entregar recebendo direto da loja."
        />
      }

      <div class="jx-home-body">
        @switch (state()) {
          @case ('offline') {
            <div class="jx-home-offline">
              <img src="take-away-amico.svg" class="jx-home-offline__icon" alt="Entregador offline" />
              <h2 class="jx-home-offline__title">Você está offline</h2>
              <p class="jx-home-offline__msg">Fique online para receber ofertas da sua área.</p>
            </div>
          }
          @case ('waiting') {
            <!-- Ganhos card -->
            <article class="jx-home-earnings">
              <span class="jx-home-earnings__label">Ganhos de hoje</span>
              <div class="jx-home-earnings__value">
                <jx-money [cents]="todayCents()" variant="display" label="Ganhos hoje" />
              </div>
              <div class="jx-home-earnings__row">
                <span class="jx-home-earnings__balance">
                  Saldo: <jx-money [cents]="balance()?.balance_cents ?? 0" />
                </span>
              </div>
            </article>

            <!-- Avaliacao -->
            @if (score(); as sc) {
              <article class="jx-home-score" (click)="goAvaliacoes()">
                <span class="jx-home-score__label">Minha avaliação</span>
                <span class="jx-home-score__value">{{ sc.avg_stars > 0 ? sc.avg_stars : '-' }} ★</span>
              </article>
            }

            <button type="button" class="jx-home-pool-btn" (click)="goSemResposta()">
              <span class="jx-home-pool-btn__label">Ver entregas sem resposta</span>
              <fa-icon [icon]="iconChevron" class="jx-home-pool-btn__arrow" aria-hidden="true" />
            </button>

            <!-- Waiting pulse -->
            <div class="jx-home-waiting" role="status">
              <span class="jx-home-pulse" aria-hidden="true"></span>
              <span>Aguardando ofertas da sua área...</span>
            </div>
          }
          @case ('busy') {
            @for (d of actives(); track d.id) {
              <article class="jx-home-busy-card">
                <span class="jx-home-busy-card__label">Entrega em andamento</span>
                @if (d.recipient_name) {
                  <strong class="jx-home-busy-card__name">{{ d.recipient_name }}</strong>
                }
                @if (d.recipient_phone) {
                  <span class="jx-home-busy-card__phone">{{ fmtPhone(d.recipient_phone) }}</span>
                }
                @if (d.dropoff_address) {
                  <span class="jx-home-busy-card__addr">
                    {{ d.dropoff_address }}@if (d.dropoff_number) {, {{ d.dropoff_number }}}@if (d.dropoff_neighborhood_name) {, {{ d.dropoff_neighborhood_name }}}
                  </span>
                }
                @if (d.dropoff_complement) {
                  <span class="jx-home-busy-card__detail">{{ d.dropoff_complement }}</span>
                }
                @if (d.dropoff_reference) {
                  <span class="jx-home-busy-card__detail jx-home-busy-card__detail--ref">{{ d.dropoff_reference }}</span>
                }
                <button type="button" class="jx-home-busy-card__btn" (click)="goActive(d.id)">
                  Abrir entrega
                </button>
              </article>
            }
          }
          @case ('offer') {
            <div class="jx-home-offer-hint">
              <span>Nova oferta!</span>
            </div>
          }
        }
      </div>

      }
    </ion-content>
  `,
  styleUrl: './inicio.page.scss',
  styles: [
    `
      .jx-home-body {
        padding: var(--jx-space-4);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }

      /* Offline state */
      .jx-home-offline {
        display: flex; flex-direction: column; align-items: center;
        gap: var(--jx-space-2); padding: var(--jx-space-6) 0; text-align: center;
      }
      .jx-home-offline__icon { width: 220px; height: auto; }
      .jx-home-offline__title { margin: 0; font-size: var(--jx-text-lg); font-weight: 700; color: var(--text); }
      .jx-home-offline__msg { margin: 0; font-size: var(--jx-text-sm); color: var(--text-muted, #888); }

      /* Earnings card */
      .jx-home-earnings {
        background: var(--brand, #e8722a); color: #fff;
        border-radius: 16px; padding: var(--jx-space-4);
        display: flex; flex-direction: column; gap: var(--jx-space-2);
      }
      .jx-home-earnings__label {
        font-size: var(--jx-text-xs); text-transform: uppercase;
        letter-spacing: 0.06em; opacity: 0.8;
      }
      .jx-home-earnings__value { font-size: 32px; font-weight: 800; }
      .jx-home-earnings__row {
        display: flex; align-items: center; justify-content: space-between;
        font-size: var(--jx-text-sm); opacity: 0.9;
      }
      .jx-home-earnings__balance { font-size: var(--jx-text-xs); }
      .jx-home-earnings .jx-home-link { color: #fff; opacity: 0.9; }
      .jx-home-earnings { --text: #fff; }

      /* Score row */
      .jx-home-score {
        display: flex; align-items: center; justify-content: space-between;
        background: #fff; border: 1px solid var(--border, #eee);
        border-radius: 12px; padding: var(--jx-space-3); cursor: pointer;
      }
      .jx-home-score__label {
        font-size: var(--jx-text-sm); font-weight: 600; color: var(--text);
      }
      .jx-home-score__value {
        font-size: var(--jx-text-sm); font-weight: 700; color: var(--brand, #e8722a);
      }

      /* Waiting */
      .jx-home-waiting {
        display: flex; align-items: center; justify-content: center;
        gap: var(--jx-space-2); color: var(--text-muted, #888);
        font-size: var(--jx-text-sm); padding: var(--jx-space-3) 0;
        height: 40vh;
      }
      .jx-home-pulse {
        width: 10px; height: 10px; border-radius: 50%;
        background: #e84e1ba3;
      }
      .jx-home-pool-btn {
        display: flex; align-items: center; justify-content: space-between;
        width: 100%; background: var(--brand, #e8722a);
        border: none; border-radius: 12px;
        padding: var(--jx-space-3); cursor: pointer;
      }
      .jx-home-pool-btn__label {
        font-size: var(--jx-text-sm); font-weight: 600; color: #fff;
      }
      .jx-home-pool-btn__arrow {
        font-size: var(--jx-text-sm); font-weight: 700; color: #fff;
      }

      /* Recent */
      .jx-home-recent-header {
        display: flex; align-items: center; justify-content: space-between;
      }
      .jx-home-section-title {
        font-size: var(--jx-text-sm); font-weight: 700; color: var(--text);
      }
      .jx-home-recent {
        list-style: none; margin: 0; padding: 0;
        display: flex; flex-direction: column;
      }
      .jx-home-recent__item {
        display: flex; align-items: center; justify-content: space-between;
        padding: var(--jx-space-3) 0;
        border-bottom: 1px solid var(--border, #eee);
      }
      .jx-home-recent__left { display: flex; flex-direction: column; gap: 2px; }
      .jx-home-recent__state { font-size: var(--jx-text-sm); font-weight: 600; color: var(--text); }
      .jx-home-recent__sub { font-size: var(--jx-text-xs); color: var(--text-muted, #888); }

      /* Busy */
      .jx-home-busy-card {
        background: var(--brand-wash, hsl(24 80% 95%));
        border: 1px solid var(--brand, #e8722a);
        border-radius: 16px; padding: var(--jx-space-4);
        display: flex; flex-direction: column; gap: var(--jx-space-2);
      }
      .jx-home-busy-card__label {
        font-size: var(--jx-text-xs); text-transform: uppercase;
        letter-spacing: 0.06em; color: var(--brand, #e8722a); font-weight: 600;
      }
      .jx-home-busy-card__name { font-size: var(--jx-text-md); font-weight: 700; color: var(--text); }
      .jx-home-busy-card__phone { font-size: var(--jx-text-sm); color: var(--text); }
      .jx-home-busy-card__addr { font-size: var(--jx-text-sm); color: var(--text); }
      .jx-home-busy-card__detail { font-size: var(--jx-text-sm); color: var(--text-muted, #888); }
      .jx-home-busy-card__detail--ref { font-style: italic; }
      .jx-home-busy-card__btn {
        min-height: 48px; border: 0; border-radius: 999px;
        background: var(--brand, #e8722a); color: #fff;
        font-size: var(--jx-text-md); font-weight: 700; cursor: pointer;
      }

      /* Offer hint */
      .jx-home-offer-hint {
        display: flex; align-items: center; justify-content: center;
        gap: var(--jx-space-2); font-size: var(--jx-text-sm);
        color: var(--brand, #e8722a); font-weight: 600;
        padding: var(--jx-space-3) 0;
      }

      .jx-home-warn-wrap { padding: 0 var(--jx-space-4); }
      .jx-home-kyc-card { display: flex; flex-direction: column; gap: 8px; padding: var(--jx-space-3); background: hsl(40 80% 92%); border: 1px solid hsl(40 80% 50%); border-radius: 12px; }
      .jx-home-kyc-msg { font-size: 13px; font-weight: 600; color: #856404; }
      .jx-home-kyc-btn { align-self: flex-start; min-height: 36px; padding: 0 var(--jx-space-3); border: 0; border-radius: 999px; background: hsl(40 80% 50%); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; }

      /* Shared */
      .jx-home-link {
        background: transparent; border: 0; padding: 0;
        color: var(--brand, #e8722a); font-weight: 600;
        cursor: pointer; font-size: var(--jx-text-xs);
      }

      /* Online until indicator */
      .jx-home-greeting { display: flex; flex-direction: column; gap: 2px; }
      .jx-home-greeting__until {
        font-size: var(--jx-text-xs); color: var(--brand, #e8722a); font-weight: 600;
      }

      /* Online duration modal */
      .jx-home-overlay {
        position: fixed; inset: 0; z-index: 200;
        background: rgba(0,0,0,0);
        display: flex; align-items: flex-end; justify-content: center;
        animation: jx-home-fade 0.2s ease forwards;
      }
      @keyframes jx-home-fade { to { background: rgba(0,0,0,0.5); } }
      .jx-home-modal {
        width: 100%; max-width: 420px;
        background: var(--jx-color-surface, #fff);
        border-radius: 20px 20px 0 0;
        padding: var(--jx-space-5);
        display: flex; flex-direction: column; gap: var(--jx-space-3);
        animation: jx-home-slide 0.3s cubic-bezier(0.22,1,0.36,1) forwards;
      }
      @keyframes jx-home-slide { from { transform: translateY(100%); } to { transform: translateY(0); } }
      .jx-home-modal__title {
        margin: 0; font-size: var(--jx-text-lg); font-weight: 700; text-align: center;
      }
      .jx-home-modal__time {
        width: 100%; min-height: 56px;
        border: 2px solid var(--brand, #e8722a);
        border-radius: var(--jx-radius-lg);
        padding: 0 var(--jx-space-3);
        font-size: var(--jx-text-2xl); font-weight: 700;
        color: var(--brand, #e8722a);
        text-align: center;
        background: transparent;
        outline: none;
        box-sizing: border-box;
      }
      .jx-home-modal__confirm {
        min-height: 52px; width: 100%;
        border: none; border-radius: 999px;
        background: var(--brand, #e8722a); color: #fff;
        font-size: var(--jx-text-md); font-weight: 700; cursor: pointer;
      }
      .jx-home-modal__cancel {
        border: 0; background: transparent; color: var(--text-muted, #888);
        font: inherit; font-size: var(--jx-text-sm); cursor: pointer;
        padding: var(--jx-space-2); text-align: center;
      }
    `,
  ],
})
export class EntregadorInicioPage implements OnInit {
  @ViewChild(AvailabilityToggleComponent) private toggleRef?: AvailabilityToggleComponent;

  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly saldo = inject(SaldoService);
  private readonly monitor = inject(OfferMonitorService);
  private readonly router = inject(Router);
  private readonly locationSvc = inject(CourierLocationService);

  protected readonly initialLoading = signal(true);
  protected readonly online = signal(false);
  protected readonly onlineUntil = signal<Date | null>(null);
  protected readonly showOnlineModal = signal(false);
  protected readonly onlineUntilTime = signal('00:00');
  private onlineTimer: ReturnType<typeof setTimeout> | null = null;
  protected readonly firstName = signal('');
  protected readonly balance = signal<Balance | null>(null);
  protected readonly todayCents = signal(0);
  protected readonly score = signal<CourierScore | null>(null);
  protected readonly recent = signal<CourierDeliveryListItem[]>([]);
  protected readonly actives = signal<CourierDelivery[]>([]);

  protected readonly kycPending = computed(() => {
    const s = this.auth.me()?.status ?? 'active';
    return s !== 'active' && s !== 'mei_pending';
  });
  protected readonly meiPending = computed(
    () => this.auth.me()?.status === 'mei_pending'
  );
  protected readonly toggleDisabled = computed(() => this.kycPending());

  // "offer" vem do monitor global — exibido pelo shell, não mais pelo início.
  protected readonly state = computed<HomeState>(() => {
    if (this.actives().length > 0) return 'busy';
    if (!this.online()) return 'offline';
    return this.monitor.offer() ? 'offer' : 'waiting';
  });

  private get courierId(): number | null {
    return this.auth.me()?.courier_id ?? null;
  }

  async ngOnInit(): Promise<void> {
    await this.auth.loadMe();
    const id = this.courierId;
    if (!id) {
      void this.router.navigate(['/entrar']);
      return;
    }
    const [balance, score, list, actives, extract, profile] = await Promise.all([
      this.saldo.balance().catch(() => null),
      this.svc.score(id),
      this.svc.listDeliveries(id).catch(() => null),
      this.svc.activeDeliveries(id).catch(() => []),
      this.saldo.extract().catch(() => []),
      this.svc.profile(id),
    ]);
    if (profile) {
      this.online.set(profile.is_online ?? false);
      this.firstName.set(profile.full_name?.split(' ')[0] ?? '');
      const until = profile.online_until ? new Date(profile.online_until) : null;
      this.onlineUntil.set(until);
      this.scheduleOfflineTimer(until);
      if (profile.is_online) this.locationSvc.start(id);
    }
    this.balance.set(balance);
    const today = new Date().toDateString();
    this.todayCents.set(
      extract
        .filter((e) => e.at && new Date(e.at).toDateString() === today)
        .reduce((sum, e) => sum + e.amount_cents, 0)
    );
    this.score.set(score);
    this.recent.set((list?.items ?? []).slice(0, 3));
    this.actives.set(actives);
    this.initialLoading.set(false);
  }

  protected async setOnline(value: boolean): Promise<void> {
    if (value) {
      // Reverte o toggle imediatamente — só vai online após confirmar o horário.
      this.toggleRef?.revert();
      this.showOnlineModal.set(true);
      return;
    }
    await this._applyAvailability(false, undefined);
  }

  protected cancelOnline(): void {
    this.showOnlineModal.set(false);
    // Toggle já está offline (revert() foi chamado ao abrir o modal).
  }

  protected async confirmOnline(): Promise<void> {
    this.showOnlineModal.set(false);
    const [h, m] = this.onlineUntilTime().split(':').map(Number);
    const now = new Date();
    const until = new Date(now);
    until.setHours(h, m, 0, 0);
    // Horário já passou hoje → coloca no próximo dia. Senão, usa hoje.
    if (until <= now) until.setDate(until.getDate() + 1);
    await this._applyAvailability(true, until.toISOString());
  }

  private async _applyAvailability(online: boolean, until?: string): Promise<void> {
    const id = this.courierId;
    if (!id) return;
    try {
      const res = await this.svc.setAvailability(id, online, until);
      this.online.set(res.is_online);
      const untilDate = res.online_until ? new Date(res.online_until) : null;
      this.onlineUntil.set(untilDate);
      this.scheduleOfflineTimer(untilDate);
      if (res.is_online) {
        this.locationSvc.start(id);
      } else {
        this.locationSvc.stop();
      }
    } catch {
      this.online.set(false);
      this.onlineUntil.set(null);
      this.scheduleOfflineTimer(null);
      this.locationSvc.stop();
    }
  }

  private scheduleOfflineTimer(until: Date | null): void {
    if (this.onlineTimer) {
      clearTimeout(this.onlineTimer);
      this.onlineTimer = null;
    }
    if (!until) return;
    const delay = until.getTime() - Date.now();
    if (delay <= 0) {
      this.online.set(false);
      this.onlineUntil.set(null);
      return;
    }
    this.onlineTimer = setTimeout(() => {
      this.online.set(false);
      this.onlineUntil.set(null);
      this.locationSvc.stop();
    }, delay);
  }

  protected fmtOnlineUntil(): string {
    const d = this.onlineUntil();
    if (!d) return '';
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }

  protected fmtPhone(e164: string | null | undefined): string {
    if (!e164) return '';
    const digits = e164.replace(/^\+55/, '');
    if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
    if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
    return e164;
  }

  protected readonly iconChevron = faChevronRight;
  protected readonly stateLabel = deliveryStateLabel;

  protected paymentLabel(method: string): string {
    const map: Record<string, string> = {
      direct: 'Pagamento direto',
      pix: 'PIX (plataforma)',
      card: 'Cartão (plataforma)',
    };
    return map[method] ?? method;
  }

  protected goProfile(): void {
    void this.router.navigate(['/entregador/perfil']);
  }
  protected goDocumentacao(): void {
    void this.router.navigate(['/entregador/perfil/documentacao']);
  }
  protected goActive(deliveryId: number): void {
    void this.router.navigate(['/entregador/entrega-ativa'], { queryParams: { deliveryId } });
  }
  protected goEntregas(): void {
    void this.router.navigate(['/entregador/entregas']);
  }
  protected goSemResposta(): void {
    void this.router.navigate(['/entregador/sem-resposta']);
  }
  protected goAvaliacoes(): void {
    void this.router.navigate(['/entregador/perfil/avaliacoes'], { queryParams: { from: 'inicio' } });
  }
}
