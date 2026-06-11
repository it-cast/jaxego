import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { StateBadgeComponent } from '../../../shared/components/state-badge/state-badge.component';
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
  imports: [TrackingTimelineComponent, StateBadgeComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-detail">
      @if (delivery(); as d) {
        <header class="jx-detail__header">
          <h1 class="jx-detail__title">Entrega #{{ d.id }}</h1>
          <jx-state-badge [state]="trackingState(d)" variant="dashboard" />
        </header>

        <div class="jx-detail__grid">
          <section class="jx-detail__main">
            <jx-tracking-timeline [state]="trackingState(d)" [entries]="[]" />
          </section>

          <aside class="jx-detail__aside">
            <dl class="jx-detail__meta">
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
})
export class EntregaDetalhePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(DeliveryService);

  protected readonly delivery = signal<DeliveryListItem | null>(null);
  protected readonly notFound = signal(false);

  async ngOnInit(): Promise<void> {
    const id = Number(this.route.snapshot.paramMap.get('id') ?? 0);
    const d = await this.service.get(id);
    if (d === null) {
      this.notFound.set(true);
      return;
    }
    this.delivery.set(d);
  }

  protected trackingState(d: DeliveryListItem): TrackingState {
    return d.state as TrackingState;
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
