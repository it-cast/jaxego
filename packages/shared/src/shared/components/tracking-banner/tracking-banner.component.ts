import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';
import type { TrackingState } from '../tracking-timeline/tracking-timeline.component';

/**
 * jx-tracking-banner — the state + ETA headline of the tracker (UI-SPEC §11).
 *
 * Renders the current state in plain words + the ETA in mono (the data-carrying
 * typography of ui-ux-pro-max). It is part of the LCP (text, render-immediate) — the
 * map is lazy and never blocks this. No glassmorphism/gradient (anti-AI-slop).
 * Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-tracking-banner',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-track-banner" role="status" aria-live="polite">
      <span class="jx-track-banner__headline">{{ headline() }}</span>
      @if (etaText()) {
        <span class="jx-track-banner__eta">{{ etaText() }}</span>
      }
    </div>
  `,
  styleUrl: './tracking-banner.component.scss',
})
export class TrackingBannerComponent {
  private readonly _state = signal<TrackingState>('CRIADA');
  private readonly _eta = signal<number | null>(null);

  @Input({ required: true })
  set state(value: TrackingState) {
    this._state.set(value);
  }

  /** ETA in seconds (null when unknown — the banner just omits it). */
  @Input()
  set etaSeconds(value: number | null) {
    this._eta.set(value);
  }

  protected readonly headline = computed(() => {
    return {
      CRIADA: 'Procurando um entregador',
      SEM_RESPOSTA: 'Ainda procurando — pode demorar um pouco mais',
      ACEITA: 'Entregador a caminho da coleta',
      COLETADA: 'A caminho de você',
      ENTREGUE: 'Pedido entregue',
      FINALIZADA: 'Entrega concluída',
      RECUSADA_NO_DESTINO: 'Não foi possível entregar',
      CANCELADA: 'Pedido cancelado',
    }[this._state()];
  });

  protected readonly etaText = computed(() => {
    const s = this._eta();
    if (s == null || this._state() === 'ENTREGUE' || this._state() === 'FINALIZADA') return null;
    const min = Math.max(1, Math.round(s / 60));
    return `Chega em cerca de ${min} min`;
  });
}
