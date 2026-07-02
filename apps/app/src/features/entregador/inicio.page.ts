import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
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
import { OfferSheetComponent } from './oferta/offer-sheet.component';
import { OfferService } from './oferta/offer.service';
import type { OfferOut, OfferResult } from './oferta/offer.models';
import {
  CourierDelivery,
  CourierDeliveryListItem,
  CourierScore,
  EntregadorService,
} from './entregador.service';
import { deliveryStateLabel } from '@jaxego/shared/util/delivery-format';

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
    OfferSheetComponent,
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
        </div>
        <jx-availability-toggle
          [isOnline]="online()"
          [disabled]="toggleDisabled()"
          disabledReason=""
          (onlineChange)="setOnline($event)"
          (seeValidation)="goProfile()"
        />
      </header>

      @if (kycPending()) {
        <div class="jx-home-warn-wrap">
          <div class="jx-home-kyc-card">
            <span class="jx-home-kyc-msg">Termine sua validação para ficar online e receber ofertas.</span>
            <button type="button" class="jx-home-kyc-btn" (click)="goDocumentacao()">Ver validação</button>
          </div>
        </div>
      }

      @if (noCoverage() && !kycPending()) {
        <div class="jx-home-warn-wrap">
          <div class="jx-home-kyc-card">
            <span class="jx-home-kyc-msg">Configure suas zonas de entrega e preços para ficar online.</span>
            <button type="button" class="jx-home-kyc-btn" (click)="goCobertura()">Ver zonas</button>
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
              <div class="jx-home-offline__icon">🛵</div>
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
                <button type="button" class="jx-home-link" (click)="goSaldo()">Ver extrato <fa-icon [icon]="iconChevron" aria-hidden="true" /></button>
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
            <article class="jx-home-busy-card">
              <span class="jx-home-busy-card__label">Entrega em andamento</span>
              <strong class="jx-home-busy-card__addr">{{ active()?.pickup_address }}</strong>
              <button type="button" class="jx-home-busy-card__btn" (click)="goActive()">
                Abrir entrega
              </button>
            </article>
          }
          @case ('offer') {
            <div class="jx-home-offer-hint">
              <span>Nova oferta!</span>
            </div>
          }
        }
      </div>

      <jx-offer-sheet
        [offer]="offer()"
        [result]="offerResult()"
        [processing]="processing()"
        (accept)="acceptOffer($event)"
        (decline)="declineOffer($event)"
      />
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
      .jx-home-offline__icon { font-size: 48px; }
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
      .jx-home-busy-card__addr { font-size: var(--jx-text-sm); color: var(--text); }
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
    `,
  ],
})
export class EntregadorInicioPage implements OnInit, OnDestroy {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly saldo = inject(SaldoService);
  private readonly offers = inject(OfferService);
  private readonly router = inject(Router);

  protected readonly initialLoading = signal(true);
  protected readonly online = signal(false);
  protected readonly firstName = signal('');
  protected readonly balance = signal<Balance | null>(null);
  protected readonly todayCents = signal(0);
  protected readonly score = signal<CourierScore | null>(null);
  protected readonly recent = signal<CourierDeliveryListItem[]>([]);
  protected readonly active = signal<CourierDelivery | null>(null);
  protected readonly offer = signal<OfferOut | null>(null);
  protected readonly offerResult = signal<OfferResult | null>(null);
  protected readonly processing = signal(false);

  private pollHandle: ReturnType<typeof setInterval> | null = null;

  protected readonly noCoverage = signal(false);
  protected readonly kycPending = computed(() => {
    const s = this.auth.me()?.status ?? 'active';
    return s !== 'active' && s !== 'mei_pending';
  });
  protected readonly meiPending = computed(
    () => this.auth.me()?.status === 'mei_pending'
  );
  protected readonly toggleDisabled = computed(
    () => this.kycPending() || this.noCoverage()
  );

  protected readonly state = computed<HomeState>(() => {
    if (this.active()) return 'busy';
    if (!this.online()) return 'offline';
    return this.offer() ? 'offer' : 'waiting';
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
    const [balance, score, list, active, extract, profile, covCount] = await Promise.all([
      this.saldo.balance().catch(() => null),
      this.svc.score(id),
      this.svc.listDeliveries(id).catch(() => null),
      this.svc.activeDelivery(id).catch(() => null),
      this.saldo.extract().catch(() => []),
      this.svc.profile(id),
      this.svc.coverageCount(id),
    ]);
    this.noCoverage.set(covCount === 0);
    if (profile) {
      this.online.set(profile.is_online ?? false);
      this.firstName.set(profile.full_name?.split(' ')[0] ?? '');
    }
    this.balance.set(balance);
    // "Liberado hoje" = soma dos créditos liberados com data de hoje (sem endpoint novo).
    const today = new Date().toDateString();
    this.todayCents.set(
      extract
        .filter((e) => e.at && new Date(e.at).toDateString() === today)
        .reduce((sum, e) => sum + e.amount_cents, 0)
    );
    this.score.set(score);
    this.recent.set((list?.items ?? []).slice(0, 3));
    this.active.set(active);
    this.initialLoading.set(false);
    this.pollHandle = setInterval(() => void this.pollOffer(), 4000);
  }

  ngOnDestroy(): void {
    if (this.pollHandle) clearInterval(this.pollHandle);
  }

  private notificationSound = new Audio('notificacao.mp3');

  private async pollOffer(): Promise<void> {
    if (!this.online() || this.active() || this.processing()) return;
    try {
      const offer = await this.offers.active();
      if (offer && !this.offer()) {
        this.notificationSound.play().catch(() => {});
      }
      if (!offer && this.offer()) {
        this.offerResult.set(null);
      }
      this.offer.set(offer);
    } catch {
      // 401 re-thrown by OfferService — interceptor handles refresh
    }
  }

  protected async setOnline(value: boolean): Promise<void> {
    const id = this.courierId;
    if (!id) return;
    try {
      const res = await this.svc.setAvailability(id, value);
      this.online.set(res.is_online);
    } catch {
      // 409 = not active; the toggle's own banner explains it. Stay offline.
      this.online.set(false);
    }
  }

  protected async acceptOffer(deliveryId: number): Promise<void> {
    this.processing.set(true);
    const result = await this.offers.accept(deliveryId);
    this.processing.set(false);
    if (result === 'won') {
      this.offer.set(null);
      this.offerResult.set(null);
      void this.router.navigate(['/entregador/entrega-ativa']);
      return;
    }
    this.offerResult.set(result); // 'lost' | 'expired' | 'error' → sheet shows outcome
    setTimeout(() => {
      this.offer.set(null);
      this.offerResult.set(null);
    }, result === 'lost' ? 5000 : 2000);
  }

  protected async declineOffer(deliveryId: number): Promise<void> {
    await this.offers.decline(deliveryId);
    this.offer.set(null);
    this.offerResult.set(null);
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

  protected goSaldo(): void {
    void this.router.navigate(['/entregador/saldo']);
  }
  protected goProfile(): void {
    void this.router.navigate(['/entregador/perfil']);
  }
  protected goDocumentacao(): void {
    void this.router.navigate(['/entregador/perfil/documentacao']);
  }
  protected goCobertura(): void {
    void this.router.navigate(['/entregador/cobertura']);
  }
  protected goActive(): void {
    void this.router.navigate(['/entregador/entrega-ativa']);
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
