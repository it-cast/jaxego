import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ErrorStateComponent } from '@jaxego/shared/state';
import { LiveMapComponent } from '@jaxego/shared/components/live-map/live-map.component';
import {
  TrackingBannerComponent,
} from '@jaxego/shared/components/tracking-banner/tracking-banner.component';
import {
  TrackingState,
  TrackingTimelineComponent,
} from '@jaxego/shared/components/tracking-timeline/tracking-timeline.component';
import { PublicTracking, PublicTrackingService } from './public-tracking.service';

/**
 * Public tracking page (tela 26) — SEM auth guard. Token-only via /r/:token.
 *
 * LCP = the banner + timeline (text, render-immediate). The map (jx-live-map) is lazy
 * and never blocks the LCP. An invalid/expired token shows jx-error-state with a
 * generic message (anti-enumeração). Refreshes every ~60s while the delivery is active.
 * Mobile-first (max-width ~480px). Dark mode reacts to the theme (DEC-001).
 */
@Component({
  selector: 'jx-public-tracking-page',
  standalone: true,
  imports: [
    TrackingBannerComponent,
    TrackingTimelineComponent,
    LiveMapComponent,
    ErrorStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-track-page">
      <header class="jx-track-page__hero">
        <div class="jx-track-page__brand">
          <span class="jx-track-page__logo" aria-hidden="true">J</span>
          <span class="jx-track-page__name">Jaxegô</span>
          <span class="jx-track-page__wordmark">rapidinho.</span>
        </div>
        <p class="jx-track-page__lead">Acompanhe sua entrega em tempo real</p>
      </header>

      <div class="jx-track-page__body">
        @if (notFound()) {
          <section class="jx-track-page__card">
            <jx-error-state
              message="Link de rastreio expirado ou entrega não encontrada. Confira com a loja."
            />
          </section>
        } @else {
          @if (data(); as d) {
            <section class="jx-track-page__card jx-track-page__card--status">
              <jx-tracking-banner [state]="state(d)" [etaSeconds]="d.eta_seconds" />
            </section>

            @if (showMap(d)) {
              <section class="jx-track-page__map">
                <jx-live-map
                  [lat]="d.courier_position!.lat"
                  [lng]="d.courier_position!.lng"
                  kind="courier"
                  label="Entregador · ao vivo"
                  [live]="true"
                  ariaLabel="Posição aproximada do entregador no mapa"
                />
              </section>
            }

            <section class="jx-track-page__card">
              <jx-tracking-timeline [state]="state(d)" [entries]="d.timeline" />
            </section>
          } @else {
            <section class="jx-track-page__card">
              <p class="jx-track-page__loading" role="status" aria-live="polite">
                Carregando o acompanhamento…
              </p>
            </section>
          }
        }

        <footer class="jx-track-page__footer">
          Acompanhamento em tempo real • dados mínimos • © OpenStreetMap
        </footer>
      </div>
    </main>
  `,
  styleUrl: './public-tracking.page.scss',
})
export class PublicTrackingPage implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(PublicTrackingService);

  protected readonly data = signal<PublicTracking | null>(null);
  protected readonly notFound = signal(false);

  private timer: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    const token = this.route.snapshot.paramMap.get('token') ?? '';
    void this.load(token);
    // Refresh while active (the page stops refreshing once terminal).
    this.timer = setInterval(() => void this.load(token), 60_000);
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }

  private async load(token: string): Promise<void> {
    const result = await this.service.get(token);
    if (!result.ok) {
      this.notFound.set(true);
      if (this.timer) clearInterval(this.timer);
      return;
    }
    this.data.set(result.data);
    if (this.isTerminal(result.data.state) && this.timer) {
      clearInterval(this.timer); // stop polling a finished delivery
    }
  }

  protected state(d: PublicTracking): TrackingState {
    return d.state as TrackingState;
  }

  protected showMap(d: PublicTracking): boolean {
    return d.courier_position != null;
  }

  private isTerminal(state: string): boolean {
    return ['FINALIZADA', 'CANCELADA', 'RECUSADA_NO_DESTINO'].includes(state);
  }
}
