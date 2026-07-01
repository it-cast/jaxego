import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { StateBadgeComponent } from '@jaxego/shared/components/state-badge/state-badge.component';
import { LiveMapComponent } from '@jaxego/shared/components/live-map/live-map.component';
import {
  packageLabel as fmtPackage,
} from '@jaxego/shared/util/delivery-format';
import {
  TrackingState,
  TrackingTimelineComponent,
} from '@jaxego/shared/components/tracking-timeline/tracking-timeline.component';
import { DeliveryListItem } from '@jaxego/shared/models/delivery.models';
import { DeliveryService } from '../entregas/delivery.service';
import { FavoritosService } from '../favoritos/favoritos.service';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStar, faBan } from '@fortawesome/free-solid-svg-icons';

/**
 * Store delivery detail (tela 13). Reuses jx-tracking-timeline + jx-state-badge.
 *
 * Responsive 2-column ≥760px collapses to 1 (responsive-breakpoint-strategy). The
 * cancel button DECLARES the cost in its label (RN-004 — "Cancelar (cobra 100% +
 * retorno)") so the store sees the consequence before acting. The recipient phone is
 * already masked by the backend (RN-022 / TH-04). The public tracking link /r/{token}
 * is shown for sharing.
 */
@Component({
  selector: 'jx-entrega-detalhe-page',
  standalone: true,
  imports: [
    FormsModule,
    TrackingTimelineComponent,
    StateBadgeComponent,
    LiveMapComponent,
    FaIconComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-detail">
      @if (delivery(); as d) {
        <header class="jx-detail__header">
          <h1 class="jx-detail__title">Entrega #{{ d.id }}</h1>
          <jx-state-badge [state]="trackingState(d)" variant="dashboard" />
        </header>

        @if (d.state === 'AGENDADA') {
          <div class="jx-detail__scheduled" role="status">
            ⏰ Entrega agendada para {{ fmtScheduled(d.scheduled_at) }}. O entregador será chamado automaticamente nesse horário.
          </div>
        }
        @if (trackingState(d) === 'CRIADA') {
          <div class="jx-detail__searching" role="status" aria-live="polite">
            <span class="jx-detail__spinner" aria-hidden="true"></span>
            Procurando entregador… a oferta foi enviada aos entregadores online da área.
          </div>
        }
        @if (d.state === 'SEM_RESPOSTA') {
          <div class="jx-detail__no-response" role="status">
            ⏳ Ainda não encontramos um entregador disponível — pode demorar um pouco mais. Você pode cancelar a qualquer momento, sem custo.
          </div>
        }

        <div class="jx-detail__grid">
          <section class="jx-detail__main">
            @if (coords(d); as c) {
              <jx-live-map [lat]="c.lat" [lng]="c.lng" ariaLabel="Mapa do destino da entrega" />
            }
            <jx-tracking-timeline [state]="trackingState(d)" [entries]="[]" />
          </section>

          <aside class="jx-detail__aside">
            <dl class="jx-detail__meta">
              @if (packageLabel(d)) {
                <dt>Pacote</dt>
                <dd>{{ packageLabel(d) }}</dd>
              }
              <dt>Destinatário</dt>
              <dd>{{ d.recipient_name ?? '—' }}</dd>
              <dt>Telefone</dt>
              <dd class="jx-detail__mono">{{ d.recipient_phone_masked ?? '—' }}</dd>
              @if (d.courier_id) {
                <dt>Entregador</dt>
                <dd>{{ d.courier_name ?? '—' }}</dd>
              }
              <dt>Link de rastreio</dt>
              <dd>
                <a class="jx-detail__link" [href]="'/r/' + d.public_token">/r/{{ d.public_token }}</a>
              </dd>
            </dl>

            @if (canCancel(d)) {
              <button type="button" class="jx-detail__cancel" (click)="cancel(d)">
                {{ cancelLabel(d) }}
              </button>
            }

            @if (d.state === 'FINALIZADA' && d.courier_id) {
              <div class="jx-detail__courier-actions">
                <button
                  type="button"
                  class="jx-detail__fav-btn"
                  [class.jx-detail__fav-btn--active]="isFavorited()"
                  [disabled]="favProcessing() || isBlocked()"
                  (click)="toggleFavorite(d.courier_id!)"
                >
                  <fa-icon [icon]="iconStar" aria-hidden="true" />
                  {{ isFavorited() ? 'Favoritado' : 'Favoritar' }}
                </button>
                <button
                  type="button"
                  class="jx-detail__block-btn"
                  [class.jx-detail__block-btn--active]="isBlocked()"
                  [disabled]="blockProcessing() || isFavorited()"
                  (click)="toggleBlock(d.courier_id!)"
                >
                  <fa-icon [icon]="iconBan" aria-hidden="true" />
                  {{ isBlocked() ? 'Bloqueado' : 'Bloquear' }}
                </button>
              </div>
            }

            @if (d.state === 'FINALIZADA' && !rated()) {
              <section class="jx-detail__rating">
                <h3 class="jx-detail__rating-title">Avaliar entregador</h3>
                <div class="jx-detail__stars">
                  @for (s of [1, 2, 3, 4, 5]; track s) {
                    <button
                      type="button"
                      class="jx-detail__star"
                      [class.jx-detail__star--on]="s <= selectedStars()"
                      (click)="selectedStars.set(s)"
                      [attr.aria-label]="s + ' estrela' + (s > 1 ? 's' : '')"
                    >
                      ★
                    </button>
                  }
                </div>
                <textarea
                  class="jx-detail__comment"
                  [(ngModel)]="ratingComment"
                  placeholder="Comentario (opcional)"
                  maxlength="500"
                  rows="2"
                ></textarea>
                <button
                  type="button"
                  class="jx-detail__rate-btn"
                  [disabled]="selectedStars() === 0 || ratingSubmitting()"
                  (click)="submitRating(d)"
                >
                  {{ ratingSubmitting() ? 'Enviando...' : 'Enviar avaliacao' }}
                </button>
              </section>
            }

            @if (rated()) {
              <section class="jx-detail__rating-done">
                <h3 class="jx-detail__rating-title">Sua avaliacao</h3>
                <div class="jx-detail__stars-display">
                  @for (s of [1, 2, 3, 4, 5]; track s) {
                    <span class="jx-detail__star-fixed" [class.jx-detail__star-fixed--on]="s <= selectedStars()">★</span>
                  }
                </div>
                @if (ratingComment.trim()) {
                  <p class="jx-detail__rating-comment">"{{ ratingComment }}"</p>
                }
                @if (justRated()) {
                  <p class="jx-detail__rated-msg">Avaliacao enviada. Obrigado!</p>
                }
              </section>
            }
          </aside>
        </div>
      } @else if (notFound()) {
        <p class="jx-detail__empty" role="status">Entrega não encontrada.</p>
      } @else {
        <p class="jx-detail__empty" role="status" aria-live="polite">Carregando…</p>
      }
    </main>
  `,
  styleUrl: './entrega-detalhe.page.scss',
  styles: [
    `
      .jx-detail__no-response {
        background: var(--warning-bg);
        border: 1px solid var(--warning);
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-3);
        color: var(--text);
        font-size: var(--jx-text-sm);
        margin-bottom: var(--jx-space-3);
      }
      .jx-detail__searching {
        display: flex;
        align-items: center;
        gap: var(--jx-space-2);
        background: var(--jx-color-brand-50);
        border: 1px solid var(--jx-color-brand-100);
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-3);
        color: var(--jx-color-brand-700, var(--brand));
        font-size: var(--jx-text-sm);
        margin-bottom: var(--jx-space-3);
      }
      .jx-detail__spinner {
        width: 16px;
        height: 16px;
        border: 2px solid var(--jx-color-brand-200);
        border-top-color: var(--jx-color-brand-500);
        border-radius: var(--jx-radius-full);
        animation: jx-spin 0.9s linear infinite;
      }
      @keyframes jx-spin {
        to {
          transform: rotate(360deg);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .jx-detail__spinner {
          animation: none;
        }
      }
    `,
  ],
})
export class EntregaDetalhePage implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(DeliveryService);
  private readonly favService = inject(FavoritosService);

  protected readonly iconStar = faStar;
  protected readonly iconBan = faBan;

  protected readonly delivery = signal<DeliveryListItem | null>(null);
  protected readonly notFound = signal(false);
  protected readonly selectedStars = signal(0);
  protected readonly rated = signal(false);
  protected readonly justRated = signal(false);
  protected readonly ratingSubmitting = signal(false);
  protected readonly isFavorited = signal(false);
  protected readonly favProcessing = signal(false);
  protected readonly isBlocked = signal(false);
  protected readonly blockProcessing = signal(false);
  protected ratingComment = '';

  private deliveryId = 0;
  private pollHandle: ReturnType<typeof setInterval> | null = null;

  async ngOnInit(): Promise<void> {
    this.deliveryId = Number(this.route.snapshot.paramMap.get('id') ?? 0);
    await this.load();
    // F4.1: while CRIADA (no courier yet), poll until a courier accepts.
    this.pollHandle = setInterval(() => void this.poll(), 5000);
  }

  ngOnDestroy(): void {
    if (this.pollHandle) clearInterval(this.pollHandle);
  }

  private async load(): Promise<void> {
    const d = await this.service.get(this.deliveryId);
    if (d === null) {
      this.notFound.set(true);
      return;
    }
    this.delivery.set(d);
    if (d.state === 'FINALIZADA') {
      const existing = await this.service.getRating(d.id);
      if (existing) {
        this.selectedStars.set(existing.stars);
        this.ratingComment = existing.comment ?? '';
        this.rated.set(true);
      }
      if (d.courier_id) {
        const [favs, blocks] = await Promise.all([
          this.favService.listFavorites(),
          this.favService.listBlocks(),
        ]);
        this.isFavorited.set(favs.some(f => f.courier_id === d.courier_id));
        this.isBlocked.set(blocks.some(b => b.courier_id === d.courier_id));
      }
    }
  }

  private async poll(): Promise<void> {
    const state = this.delivery()?.state;
    if (state !== 'CRIADA' && state !== 'AGENDADA' && state !== 'SEM_RESPOSTA') {
      if (this.pollHandle) clearInterval(this.pollHandle);
      this.pollHandle = null;
      return;
    }
    await this.load();
  }

  protected trackingState(d: DeliveryListItem): TrackingState {
    // AGENDADA não tem representação no tracking timeline — mostra como CRIADA
    if (d.state === 'AGENDADA') return 'CRIADA';
    return d.state as TrackingState;
  }

  protected readonly packageLabel = fmtPackage;

  /** Coords do destino para o mapa, ou null (lint/type-safe). */
  protected coords(d: DeliveryListItem): { lat: number; lng: number } | null {
    return typeof d.dropoff_lat === 'number' && typeof d.dropoff_lng === 'number'
      ? { lat: d.dropoff_lat, lng: d.dropoff_lng }
      : null;
  }

  protected canCancel(d: DeliveryListItem): boolean {
    return ['AGENDADA', 'CRIADA', 'SEM_RESPOSTA', 'ACEITA', 'COLETADA'].includes(d.state);
  }

  /** RN-004 cost declared IN the label (br/ux-copywriting-ptbr). */
  protected cancelLabel(d: DeliveryListItem): string {
    if (d.state === 'AGENDADA') return 'Cancelar (sem custo)';
    if (d.state === 'CRIADA') return 'Cancelar (sem custo)';
    if (d.state === 'SEM_RESPOSTA') return 'Cancelar (sem custo)';
    if (d.state === 'ACEITA') return 'Cancelar (cobra 50%)';
    return 'Cancelar (cobra 100% + retorno)';
  }

  protected fmtScheduled(iso: string | null | undefined): string {
    if (!iso) return '';
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  protected async submitRating(d: DeliveryListItem): Promise<void> {
    if (this.selectedStars() === 0 || this.ratingSubmitting()) return;
    this.ratingSubmitting.set(true);
    const ok = await this.service.rate(d.id, this.selectedStars(), this.ratingComment.trim() || null);
    this.ratingSubmitting.set(false);
    if (ok) {
      this.rated.set(true);
      this.justRated.set(true);
    }
  }

  protected async toggleFavorite(courierId: number): Promise<void> {
    this.favProcessing.set(true);
    try {
      if (this.isFavorited()) {
        await this.favService.removeFavorite(courierId);
        this.isFavorited.set(false);
      } else {
        await this.favService.addFavorite(courierId);
        this.isFavorited.set(true);
      }
    } catch { /* already exists or not found — ignore */ }
    this.favProcessing.set(false);
  }

  protected async toggleBlock(courierId: number): Promise<void> {
    this.blockProcessing.set(true);
    try {
      if (this.isBlocked()) {
        await this.favService.removeBlock(courierId);
        this.isBlocked.set(false);
      } else {
        await this.favService.addBlock(courierId);
        this.isBlocked.set(true);
        this.isFavorited.set(false);
      }
    } catch { /* already exists or not found */ }
    this.blockProcessing.set(false);
  }

  protected async cancel(d: DeliveryListItem): Promise<void> {
    const ok = await this.service.cancel(d.id);
    if (ok) {
      this.delivery.set({ ...d, state: 'CANCELADA' });
    }
  }
}
