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
import { AuthService } from '../../core/auth/auth.service';
import {
  MoneyComponent,
  ScoreChipComponent,
  type ScoreLevel,
} from '../../shared/components';
import { EmptyStateComponent, WarnBannerComponent } from '../../shared/state';
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
import { deliveryStateLabel } from '../../shared/util/delivery-format';

/** Mutually-exclusive dispatch states on the home (UI-SPEC §2.3). */
type HomeState = 'offline' | 'waiting' | 'offer' | 'busy';

const VALID_LEVELS: ScoreLevel[] = [
  'probation',
  'bronze',
  'prata',
  'ouro',
  'diamante',
];

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
    EmptyStateComponent,
    WarnBannerComponent,
    AvailabilityToggleComponent,
    OfferSheetComponent,
    MoneyComponent,
    ScoreChipComponent,
  ],
  template: `
    <ion-content>
      <header class="jx-home-header">
        <div class="jx-home-greeting">
          <span class="jx-home-greeting__hi">Olá!</span>
        </div>
        <jx-availability-toggle
          [isOnline]="online()"
          [disabled]="kycPending()"
          (onlineChange)="setOnline($event)"
          (seeValidation)="goProfile()"
        />
      </header>

      @if (meiPending()) {
        <jx-warn-banner
          message="Você ainda não tem MEI ativo. Pode entregar recebendo direto da loja. Para receber pela plataforma, regularize seu MEI."
        />
      }

      <div class="jx-home-body">
        @switch (state()) {
          @case ('offline') {
            <jx-empty-state
              icon="🛵"
              title="Você está offline"
              message="Fique online para receber ofertas da sua área."
            />
          }
          @case ('waiting') {
            <div class="jx-home-cards">
              <article class="jx-home-card jx-home-card--dark">
                <span class="jx-home-card__eyebrow">Liberado hoje</span>
                <jx-money [cents]="todayCents()" variant="display" label="Ganhos liberados hoje" />
                <div class="jx-home-card--row" style="padding:0">
                  <span class="jx-home-muted">
                    Saldo p/ saque:
                    <jx-money [cents]="balance()?.balance_cents ?? 0" />
                  </span>
                  <button type="button" class="jx-home-link" (click)="goSaldo()">
                    Ver extrato →
                  </button>
                </div>
              </article>

              @if (score(); as sc) {
                <article class="jx-home-card jx-home-card--row">
                  <div>
                    <span class="jx-home-card__eyebrow">Seu score</span>
                    <jx-score-chip [level]="level()" [value]="sc.total_score" />
                  </div>
                  <button type="button" class="jx-home-link" (click)="goProfile()">
                    Por quê? →
                  </button>
                </article>
              }

              <div class="jx-home-waiting" role="status">
                <span class="jx-home-pulse" aria-hidden="true"></span>
                <span>Aguardando ofertas da sua área…</span>
              </div>

              @if (recent().length) {
                <div class="jx-home-card--row" style="padding:0">
                  <span class="jx-home-card__eyebrow">Entregas recentes</span>
                  <button type="button" class="jx-home-link" (click)="goEntregas()">
                    Ver todas →
                  </button>
                </div>
                @for (d of recent(); track d.id) {
                  <article class="jx-home-card jx-home-card--row">
                    <div>
                      <strong>{{ stateLabel(d.state) }}</strong>
                      <p class="jx-home-muted">{{ paymentLabel(d.payment_method) }}</p>
                    </div>
                    <jx-money [cents]="d.estimate_min_cents ?? d.fee_cents" />
                  </article>
                }
              }
            </div>
          }
          @case ('busy') {
            <article class="jx-home-card jx-home-card--dest">
              <span class="jx-home-card__eyebrow">Você está em uma entrega</span>
              <strong>{{ active()?.pickup_address }}</strong>
              <button type="button" class="jx-home-primary" (click)="goActive()">
                Abrir entrega
              </button>
            </article>
          }
          @case ('offer') {
            <jx-empty-state icon="🔔" title="Nova oferta" message="Veja abaixo." />
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
    </ion-content>
  `,
  styleUrl: './inicio.page.scss',
  styles: [
    `
      .jx-home-body {
        padding: var(--jx-space-4);
      }
      .jx-home-cards {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-home-card {
        background: var(--jx-color-surface);
        border: 1px solid var(--jx-color-neutral-200);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-1);
      }
      .jx-home-card--row {
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
      }
      .jx-home-card--dark {
        background: var(--jx-color-neutral-800);
        color: var(--jx-neutral-50);
        border: 0;
      }
      .jx-home-card--dest {
        background: var(--jx-color-brand-50);
        border-color: var(--jx-color-brand-100);
      }
      .jx-home-card__eyebrow {
        font-family: var(--jx-font-mono);
        font-size: var(--jx-text-xs);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--jx-color-neutral-500);
      }
      .jx-home-card--dark .jx-home-card__eyebrow {
        color: var(--jx-color-brand-300);
      }
      .jx-home-muted {
        margin: 0;
        font-size: var(--jx-text-sm);
        color: var(--jx-color-neutral-500);
      }
      .jx-home-link {
        background: transparent;
        border: 0;
        padding: 0;
        color: var(--jx-color-brand-600);
        font-weight: 600;
        cursor: pointer;
        font-size: var(--jx-text-sm);
        align-self: flex-start;
      }
      .jx-home-card--dark .jx-home-link {
        color: var(--jx-color-brand-300);
      }
      .jx-home-primary {
        border: 0;
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-3);
        background: var(--jx-color-brand-500);
        color: var(--jx-neutral-50);
        font-weight: 700;
        cursor: pointer;
        min-height: 48px;
      }
      .jx-home-waiting {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
        color: var(--jx-color-neutral-500);
        font-size: var(--jx-text-sm);
        padding: var(--jx-space-2) 0;
      }
      .jx-home-pulse {
        width: 8px;
        height: 8px;
        border-radius: var(--jx-radius-full);
        background: var(--jx-color-brand-500);
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

  protected readonly online = signal(false);
  protected readonly balance = signal<Balance | null>(null);
  protected readonly todayCents = signal(0);
  protected readonly score = signal<CourierScore | null>(null);
  protected readonly recent = signal<CourierDeliveryListItem[]>([]);
  protected readonly active = signal<CourierDelivery | null>(null);
  protected readonly offer = signal<OfferOut | null>(null);
  protected readonly offerResult = signal<OfferResult | null>(null);
  protected readonly processing = signal(false);

  private pollHandle: ReturnType<typeof setInterval> | null = null;

  protected readonly kycPending = computed(
    () => (this.auth.me()?.status ?? 'active') !== 'active'
  );
  protected readonly meiPending = computed(
    () => this.auth.me()?.status === 'mei_pending'
  );

  protected readonly state = computed<HomeState>(() => {
    if (this.active()) return 'busy';
    if (!this.online()) return 'offline';
    return this.offer() ? 'offer' : 'waiting';
  });

  protected readonly level = computed<ScoreLevel>(() => {
    const lvl = this.score()?.level as ScoreLevel | undefined;
    return lvl && VALID_LEVELS.includes(lvl) ? lvl : 'probation';
  });

  private get courierId(): number | null {
    return this.auth.me()?.courier_id ?? null;
  }

  async ngOnInit(): Promise<void> {
    const id = this.courierId;
    if (!id) return;
    const [balance, score, list, active, extract] = await Promise.all([
      this.saldo.balance().catch(() => null),
      this.svc.score(id),
      this.svc.listDeliveries(id).catch(() => null),
      this.svc.activeDelivery(id).catch(() => null),
      this.saldo.extract().catch(() => []),
    ]);
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
    this.pollHandle = setInterval(() => void this.pollOffer(), 4000);
  }

  ngOnDestroy(): void {
    if (this.pollHandle) clearInterval(this.pollHandle);
  }

  private async pollOffer(): Promise<void> {
    if (!this.online() || this.active() || this.offer() || this.processing()) return;
    this.offer.set(await this.offers.active());
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
    }, 2000);
  }

  protected async declineOffer(deliveryId: number): Promise<void> {
    await this.offers.decline(deliveryId);
    this.offer.set(null);
    this.offerResult.set(null);
  }

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
  protected goActive(): void {
    void this.router.navigate(['/entregador/entrega-ativa']);
  }
  protected goEntregas(): void {
    void this.router.navigate(['/entregador/entregas']);
  }
}
