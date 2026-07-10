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
} from '@jaxego/shared/components/tracking-timeline/tracking-timeline.component';
import { DeliveryListItem } from '@jaxego/shared/models/delivery.models';
import { DeliveryService } from '../entregas/delivery.service';
import { FavoritosService } from '../favoritos/favoritos.service';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStar, faBan, faCopy, faCheck } from '@fortawesome/free-solid-svg-icons';

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
    StateBadgeComponent,
    LiveMapComponent,
    FaIconComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-detail">
      @if (delivery(); as d) {
        <!-- Header: ID + badge -->
        <header class="jx-detail__header">
          <h1 class="jx-detail__title">Entrega #{{ d.id }}</h1>
          @if (d.state !== 'AGUARDANDO_PAGAMENTO') {
            <jx-state-badge [state]="trackingState(d)" variant="dashboard" />
          } @else {
            <span class="jx-detail__pix-badge">Aguardando pagamento</span>
          }
        </header>

        <!-- ── Modo PIX: aguardando pagamento ───────────────────────────── -->
        @if (d.state === 'AGUARDANDO_PAGAMENTO') {
          <div class="jx-detail__pix-screen" role="status" aria-live="polite">
            <p class="jx-detail__pix-hint">Escaneie o QR code ou copie o código para pagar via PIX. O entregador será chamado automaticamente após a confirmação.</p>
            @if (d.pix_qr_code_base64) {
              <img
                class="jx-detail__pix-qr"
                [src]="d.pix_qr_code_base64"
                alt="QR Code PIX"
              />
            }
            @if (d.pix_qr_code) {
              <div class="jx-detail__pix-copy-row">
                <input
                  class="jx-detail__pix-code"
                  [value]="d.pix_qr_code"
                  readonly
                  aria-label="Código PIX copia e cola"
                />
                <button
                  type="button"
                  class="jx-detail__pix-copy-btn"
                  (click)="copyPix(d.pix_qr_code)"
                  [attr.aria-label]="pixCopied() ? 'Copiado' : 'Copiar código PIX'"
                >
                  @if (pixCopied()) {
                    <fa-icon [icon]="iconCheck" />
                  } @else {
                    <fa-icon [icon]="iconCopy" />
                  }
                </button>
              </div>
              @if (pixCopied()) {
                <p class="jx-detail__pix-copied-msg">Código copiado!</p>
              }
            }
            <p class="jx-detail__pix-waiting">Aguardando confirmação de pagamento…</p>
          </div>

        } @else {

        <!-- ── Modo normal ───────────────────────────────────────────────── -->

        <!-- Banners contextuais -->
        @if (d.state === 'AGENDADA') {
          <div class="jx-detail__banner jx-detail__banner--info" role="status">
            ⏰ Agendada para {{ fmtScheduled(d.scheduled_at) }}. O entregador será chamado automaticamente.
          </div>
        }
        <!-- Timeline horizontal -->
        <div class="jx-detail__htl" aria-label="Progresso da entrega">
          @for (step of hSteps(d); track step.key; let last = $last) {
            <div class="jx-detail__htl-step" [class.jx-detail__htl-step--done]="step.done" [class.jx-detail__htl-step--current]="step.current">
              <div class="jx-detail__htl-dot">{{ step.done ? '●' : step.current ? '◉' : '○' }}</div>
              <div class="jx-detail__htl-label">{{ step.label }}</div>
            </div>
            @if (!last) {
              <div class="jx-detail__htl-line" [class.jx-detail__htl-line--done]="step.done"></div>
            }
          }
        </div>

        <!-- GIF de busca (abaixo da timeline) -->
        @if (trackingState(d) === 'CRIADA') {
          <div class="jx-detail__searching" role="status" aria-live="polite">
            <img src="/searching.gif" alt="" aria-hidden="true" class="jx-detail__searching-gif" />
            <span>Procurando entregador… a oferta foi enviada aos entregadores online da área.</span>
          </div>
        }

        <!-- Grid principal -->
        <div class="jx-detail__grid">

          <!-- Coluna esquerda: conteúdo -->
          <section class="jx-detail__main">

            <!-- Card: Endereço de entrega -->
            <div class="jx-detail__card">
              <h2 class="jx-detail__card-title">Endereço de entrega</h2>
              <dl class="jx-detail__dl">
                @if (d.dropoff_address) {
                  <dt>Rua / Logradouro</dt>
                  <dd>{{ d.dropoff_address }}@if (d.dropoff_number) {, {{ d.dropoff_number }}}</dd>
                }
                @if (d.dropoff_neighborhood_name) {
                  <dt>Bairro</dt>
                  <dd>{{ d.dropoff_neighborhood_name }}</dd>
                }
                @if (d.dropoff_complement) {
                  <dt>Complemento</dt>
                  <dd>{{ d.dropoff_complement }}</dd>
                }
                @if (d.dropoff_reference) {
                  <dt>Referência</dt>
                  <dd class="jx-detail__italic">{{ d.dropoff_reference }}</dd>
                }
                @if (d.pickup_address) {
                  <dt>Coleta (loja)</dt>
                  <dd>{{ d.pickup_address }}@if (d.pickup_neighborhood) { — {{ d.pickup_neighborhood }}}</dd>
                }
              </dl>
            </div>

            <!-- Linha: Destinatário + Entregador, lado a lado -->
            <div class="jx-detail__row">
              <div class="jx-detail__card">
                <h2 class="jx-detail__card-title">Destinatário</h2>
                <dl class="jx-detail__dl">
                  <dt>Nome</dt>
                  <dd>{{ d.recipient_name ?? '—' }}</dd>
                  <dt>Telefone</dt>
                  <dd class="jx-detail__mono">{{ fmtPhone(d.recipient_phone) }}</dd>
                  @if (d.team_names && d.team_names.length) {
                    <dt>Equipes acionadas</dt>
                    <dd>{{ d.team_names.join(', ') }}</dd>
                  }
                  @if (d.price_cents != null) {
                    <dt>Valor</dt>
                    <dd class="jx-detail__price">{{ fmtCents(d.price_cents) }}</dd>
                  }
                  <dt>Link de rastreio</dt>
                  <dd>
                    <a class="jx-detail__link" [href]="'/r/' + d.public_token">/r/{{ d.public_token }}</a>
                  </dd>
                </dl>
              </div>

              <!-- Card: Entregador (só aparece após a entrega ser aceita) -->
              @if (d.courier_id) {
                <div class="jx-detail__card">
                  <h2 class="jx-detail__card-title">Entregador</h2>
                  <dl class="jx-detail__dl">
                    <dt>Nome</dt>
                    <dd>{{ d.courier_name ?? '—' }}</dd>
                    <dt>Telefone</dt>
                    <dd class="jx-detail__mono">{{ fmtPhone(d.courier_phone) }}</dd>
                    @if (d.courier_vehicle_type) {
                      <dt>Veículo</dt>
                      <dd>
                        {{ vehicleLabel(d.courier_vehicle_type) }}@if (d.courier_vehicle_plate) { — {{ d.courier_vehicle_plate }}}
                      </dd>
                    }
                    <dt>Avaliação</dt>
                    <dd>
                      @if (d.courier_rating != null) {
                        <fa-icon [icon]="iconStar" aria-hidden="true" class="jx-detail__courier-star" />
                        {{ d.courier_rating }} ({{ d.courier_rating_count }} avaliaç{{ d.courier_rating_count === 1 ? 'ão' : 'ões' }})
                      } @else {
                        Ainda sem avaliações
                      }
                    </dd>
                    <dt>Entregas concluídas</dt>
                    <dd>{{ d.courier_total_deliveries ?? 0 }}</dd>
                    @if (d.price_cents != null) {
                      <dt>Valor da corrida</dt>
                      <dd class="jx-detail__price">{{ fmtCents(d.price_cents) }}</dd>
                    }
                    @if (d.courier_since) {
                      <dt>Na plataforma desde</dt>
                      <dd>{{ fmtDate(d.courier_since) }}</dd>
                    }
                  </dl>
                </div>
              }
            </div>

            <!-- Mapa quadrado -->
            @if (coords(d); as c) {
              <div class="jx-detail__map-wrap">
                <jx-live-map [lat]="c.lat" [lng]="c.lng" ariaLabel="Mapa do destino da entrega" />
              </div>
            }
          </section>

          <!-- Coluna direita: meta + ações -->
          <aside class="jx-detail__aside">

            <!-- Card: Itens / Observações -->
            @if (d.items_description || (d.items_quantity && d.items_quantity > 1) || d.notes || packageLabel(d)) {
              <div class="jx-detail__card">
                <h2 class="jx-detail__card-title">Itens e observações</h2>
                <dl class="jx-detail__dl">
                  @if (d.items_description) {
                    <dt>Descrição</dt>
                    <dd>{{ d.items_description }}</dd>
                  }
                  @if (d.items_quantity && d.items_quantity > 1) {
                    <dt>Quantidade</dt>
                    <dd>{{ d.items_quantity }} itens</dd>
                  }
                  @if (packageLabel(d)) {
                    <dt>Pacote</dt>
                    <dd>{{ packageLabel(d) }}</dd>
                  }
                  @if (d.notes) {
                    <dt>Observações</dt>
                    <dd class="jx-detail__italic">{{ d.notes }}</dd>
                  }
                </dl>
              </div>
            }

            <!-- Ação: Cancelar -->
            @if (canCancel(d)) {
              <button type="button" class="jx-detail__cancel" (click)="cancel(d)">
                {{ cancelLabel(d) }}
              </button>
            }

            <!-- Ações: Favoritar / Bloquear entregador -->
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

            <!-- Avaliação -->
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
                    >★</button>
                  }
                </div>
                <textarea
                  class="jx-detail__comment"
                  [(ngModel)]="ratingComment"
                  placeholder="Comentário (opcional)"
                  maxlength="500"
                  rows="2"
                ></textarea>
                <button
                  type="button"
                  class="jx-detail__rate-btn"
                  [disabled]="selectedStars() === 0 || ratingSubmitting()"
                  (click)="submitRating(d)"
                >{{ ratingSubmitting() ? 'Enviando...' : 'Enviar avaliação' }}</button>
              </section>
            }

            @if (rated()) {
              <section class="jx-detail__rating-done">
                <h3 class="jx-detail__rating-title">Sua avaliação</h3>
                <div class="jx-detail__stars-display">
                  @for (s of [1, 2, 3, 4, 5]; track s) {
                    <span class="jx-detail__star-fixed" [class.jx-detail__star-fixed--on]="s <= selectedStars()">★</span>
                  }
                </div>
                @if (ratingComment.trim()) {
                  <p class="jx-detail__rating-comment">"{{ ratingComment }}"</p>
                }
                @if (justRated()) {
                  <p class="jx-detail__rated-msg">Avaliação enviada. Obrigado!</p>
                }
              </section>
            }
          </aside>
        </div>
        } <!-- end @else (modo normal) -->

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
      /* Banners */
      .jx-detail__banner {
        padding: var(--jx-space-3) var(--jx-space-4);
        border-radius: var(--jx-radius-md);
        font-size: var(--jx-text-sm);
        margin-bottom: var(--jx-space-2);
      }
      .jx-detail__banner--info {
        background: var(--brand-wash);
        border-left: 3px solid var(--brand);
        color: var(--text);
      }
      .jx-detail__banner--warn {
        background: var(--warning-bg);
        border: 1px solid var(--warning);
        color: var(--text);
      }
      /* Searching GIF */
      .jx-detail__searching {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--jx-space-2);
        background: var(--jx-color-brand-50);
        border: 1px solid var(--jx-color-brand-100);
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-3);
        color: var(--jx-color-brand-700, var(--brand));
        font-size: var(--jx-text-sm);
        margin-bottom: var(--jx-space-3);
        text-align: center;
      }
      .jx-detail__searching-gif {
        width: min(20em, 100%);
        height: auto;
        border-radius: var(--jx-radius-sm);
      }
      /* Timeline horizontal */
      .jx-detail__htl {
        display: flex;
        align-items: center;
        gap: 0;
        overflow-x: auto;
        padding: var(--jx-space-3) 0;
        scrollbar-width: none;
      }
      .jx-detail__htl::-webkit-scrollbar { display: none; }
      .jx-detail__htl-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        min-width: 72px;
        color: var(--text-muted);
        font-size: var(--jx-text-xs);
        text-align: center;
        flex-shrink: 0;
      }
      .jx-detail__htl-step--done {
        color: var(--text);
        .jx-detail__htl-dot { color: var(--success, #16a34a); }
      }
      .jx-detail__htl-step--current {
        color: var(--text);
        .jx-detail__htl-dot { color: var(--brand); font-size: 1.1em; }
        .jx-detail__htl-label { font-weight: 600; color: var(--brand); }
      }
      .jx-detail__htl-dot { font-size: 1em; line-height: 1; }
      .jx-detail__htl-label { line-height: 1.2; }
      .jx-detail__htl-line {
        flex: 1;
        min-width: 16px;
        height: 1px;
        background: var(--border-strong);
        align-self: flex-start;
        margin-top: 0.5em;
        flex-shrink: 0;
      }
      .jx-detail__htl-line--done { background: var(--success, #16a34a); }
      /* Cards */
      .jx-detail__card {
        background: var(--surface-elevated, var(--surface));
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-4);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
      }
      .jx-detail__card-title {
        margin: 0;
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-semibold);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
      }
      /* DL grid */
      .jx-detail__dl {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: var(--jx-space-1) var(--jx-space-3);
        margin: 0;
        font-size: var(--jx-text-sm);
        dt { color: var(--text-muted); white-space: nowrap; }
        dd { margin: 0; color: var(--text); word-break: break-word; }
      }
      .jx-detail__italic { font-style: italic; }
      .jx-detail__price { font-weight: var(--jx-weight-semibold); color: var(--brand); }
      /* Linha Itens + Entregador lado a lado (responsive-breakpoint-strategy) */
      .jx-detail__row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: var(--jx-space-4);
        align-items: start;
      }
      .jx-detail__courier-star {
        color: var(--brand);
        margin-right: 2px;
      }
      /* Map — square */
      .jx-detail__map-wrap {
        width: 20vw;
        aspect-ratio: 1 / 1;
        border-radius: var(--jx-radius-lg);
        overflow: hidden;
        border: 1px solid var(--border);
        --jx-map-height: 100%;
      }
      .jx-detail__map-wrap jx-live-map {
        display: block;
        width: 100%;
        height: 100%;
      }
      /* PIX payment screen */
      .jx-detail__pix-badge {
        display: inline-block;
        padding: 2px var(--jx-space-2);
        border-radius: var(--jx-radius-sm);
        background: var(--brand-wash, #fff7ed);
        color: var(--brand);
        font-size: var(--jx-text-xs);
        font-weight: var(--jx-weight-semibold);
        border: 1px solid var(--brand);
      }
      .jx-detail__pix-screen {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--jx-space-3);
        padding: .5em 1em 1em;
        max-width: 420px;
        margin: var(--jx-space-4) auto 0;
      }
      .jx-detail__pix-hint {
        font-size: var(--jx-text-sm);
        color: var(--text-muted);
        text-align: center;
        margin: 0;
      }
      .jx-detail__pix-qr {
        width: 300px;
        height: 300px;
        object-fit: contain;
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-md);
        padding: .5em 1em 1em;
        background: #fff;
      }
      .jx-detail__pix-copy-row {
        display: flex;
        width: 100%;
        gap: var(--jx-space-2);
      }
      .jx-detail__pix-code {
        flex: 1;
        min-width: 0;
        padding: var(--jx-space-2) var(--jx-space-3);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-md);
        background: var(--surface-sunken);
        font-size: var(--jx-text-xs);
        font-family: monospace;
        color: var(--text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .jx-detail__pix-copy-btn {
        padding: var(--jx-space-2) var(--jx-space-3);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-md);
        background: var(--surface-elevated);
        color: var(--text);
        cursor: pointer;
        flex-shrink: 0;
        &:hover { background: var(--surface-sunken); }
      }
      .jx-detail__pix-copied-msg {
        font-size: var(--jx-text-xs);
        color: var(--success, #16a34a);
        margin: 0;
      }
      .jx-detail__pix-waiting {
        font-size: var(--jx-text-sm);
        color: var(--text-muted);
        margin: 0;
        text-align: center;
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
  protected readonly iconCopy = faCopy;
  protected readonly iconCheck = faCheck;
  protected readonly pixCopied = signal(false);

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
    const pollStates = ['CRIADA', 'AGENDADA', 'SEM_RESPOSTA', 'AGUARDANDO_PAGAMENTO'];
    if (!pollStates.includes(state ?? '')) {
      if (this.pollHandle) clearInterval(this.pollHandle);
      this.pollHandle = null;
      return;
    }
    await this.load();
  }

  protected async copyPix(code: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(code);
      this.pixCopied.set(true);
      setTimeout(() => this.pixCopied.set(false), 2500);
    } catch { /* clipboard bloqueado — sem ação */ }
  }

  protected trackingState(d: DeliveryListItem): TrackingState {
    // SEM_RESPOSTA e AGENDADA aparecem como CRIADA para a loja — o estado interno é
    // usado apenas pelo app do entregador e pelo dispatch.
    if (d.state === 'AGENDADA' || d.state === 'SEM_RESPOSTA') return 'CRIADA';
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

  protected fmtPhone(e164: string | null | undefined): string {
    if (!e164) return '—';
    // +5522988882922 → (22) 98888-2922
    const digits = e164.replace(/^\+55/, '');
    if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
    if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
    return e164;
  }

  protected fmtCents(cents: number | null | undefined): string {
    if (cents == null) return '—';
    return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  protected fmtDate(iso: string | null | undefined): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  }

  protected vehicleLabel(type: string | null | undefined): string {
    const LABELS: Record<string, string> = {
      moto: 'Moto',
      bicicleta: 'Bicicleta',
      carro: 'Carro',
      a_pe: 'A pé',
    };
    return (type && LABELS[type]) ?? type ?? '—';
  }

  protected hSteps(d: DeliveryListItem): { key: string; label: string; done: boolean; current: boolean }[] {
    const state = this.trackingState(d);
    const HAPPY: TrackingState[] = ['CRIADA', 'ACEITA', 'COLETADA', 'ENTREGUE', 'FINALIZADA'];
    const LABELS: Record<string, string> = {
      CRIADA: 'Criada', ACEITA: 'Aceita', COLETADA: 'Coletada', ENTREGUE: 'Entregue', FINALIZADA: 'Concluída',
      CANCELADA: 'Cancelada', RECUSADA_NO_DESTINO: 'Recusada', SEM_RESPOSTA: 'Sem resposta',
    };
    if (state === 'CANCELADA' || state === 'RECUSADA_NO_DESTINO') {
      return [
        { key: 'CRIADA', label: 'Criada', done: true, current: false },
        { key: state, label: LABELS[state], done: false, current: true },
      ];
    }
    const idx = HAPPY.indexOf(state);
    return HAPPY.map((s, i) => ({
      key: s,
      label: LABELS[s],
      done: i < idx,
      current: i === idx,
    }));
  }
}
