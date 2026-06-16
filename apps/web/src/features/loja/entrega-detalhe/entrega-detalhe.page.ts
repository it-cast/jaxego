import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { StateBadgeComponent } from '../../../shared/components/state-badge/state-badge.component';
import { LiveMapComponent } from '../../../shared/components/live-map/live-map.component';
import { PaymentBadgeComponent, type PaymentMethod } from '../../../shared/components';
import {
  TrackingState,
  TrackingTimelineComponent,
} from '../../../shared/components/tracking-timeline/tracking-timeline.component';
import { DeliveryListItem } from '../entregas/delivery.models';
import { DeliveryService } from '../entregas/delivery.service';

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
    TrackingTimelineComponent,
    StateBadgeComponent,
    PaymentBadgeComponent,
    LiveMapComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-detail">
      @if (delivery(); as d) {
        <header class="jx-detail__header">
          <h1 class="jx-detail__title">Entrega #{{ d.id }}</h1>
          <jx-state-badge [state]="trackingState(d)" variant="dashboard" />
          <jx-payment-badge [method]="payOf(d.payment_method)" />
        </header>

        @if (trackingState(d) === 'CRIADA') {
          <div class="jx-detail__searching" role="status" aria-live="polite">
            <span class="jx-detail__spinner" aria-hidden="true"></span>
            Procurando entregador… a oferta foi enviada aos entregadores online da área.
          </div>
        }

        <div class="jx-detail__grid">
          <section class="jx-detail__main">
            @if (d.dropoff_lat != null && d.dropoff_lng != null) {
              <jx-live-map
                [lat]="d.dropoff_lat"
                [lng]="d.dropoff_lng"
                ariaLabel="Mapa do destino da entrega"
              />
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

  protected readonly delivery = signal<DeliveryListItem | null>(null);
  protected readonly notFound = signal(false);

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
  }

  private async poll(): Promise<void> {
    if (this.delivery()?.state !== 'CRIADA') {
      if (this.pollHandle) clearInterval(this.pollHandle);
      this.pollHandle = null;
      return;
    }
    await this.load();
  }

  protected trackingState(d: DeliveryListItem): TrackingState {
    return d.state as TrackingState;
  }

  protected payOf(method: string): PaymentMethod {
    return method === 'pix' || method === 'card' ? method : 'direct';
  }

  /** "2,5 kg · 40×30×20 cm" — só as partes preenchidas. Vazio se nada. */
  protected packageLabel(d: DeliveryListItem): string {
    const parts: string[] = [];
    if (d.weight_g) parts.push(`${(d.weight_g / 1000).toLocaleString('pt-BR')} kg`);
    if (d.length_cm && d.width_cm && d.height_cm) {
      parts.push(`${d.length_cm}×${d.width_cm}×${d.height_cm} cm`);
    }
    return parts.join(' · ');
  }

  protected canCancel(d: DeliveryListItem): boolean {
    return ['CRIADA', 'ACEITA', 'COLETADA'].includes(d.state);
  }

  /** RN-004 cost declared IN the label (br/ux-copywriting-ptbr). */
  protected cancelLabel(d: DeliveryListItem): string {
    if (d.state === 'CRIADA') return 'Cancelar (sem custo)';
    if (d.state === 'ACEITA') return 'Cancelar (cobra 50%)';
    return 'Cancelar (cobra 100% + retorno)';
  }

  protected async cancel(d: DeliveryListItem): Promise<void> {
    const ok = await this.service.cancel(d.id);
    if (ok) {
      this.delivery.set({ ...d, state: 'CANCELADA' });
    }
  }
}
