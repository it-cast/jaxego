import {
  ChangeDetectionStrategy,
  Component,
  Input,
  OnDestroy,
  computed,
  signal,
} from '@angular/core';

/** Urgency phase (UI-SPEC §4.2) — drives the color, never the only signal. */
export type TimerPhase = 'calm' | 'attention' | 'urgent';

/**
 * jx-offer-timer — the COSMETIC countdown (ADR-104). The Redis TTL on the server
 * is the source of truth; this ring/number is an optimistic mirror that re-syncs
 * to the authoritative `ttlRemainingS` and NEVER decides expiration on its own.
 *
 * a11y (accessibility-pro): the seconds are mono TEXT (not color-only) and
 * announced via aria-live at MILESTONES (open / 10s / 5s / expired) — not every
 * second. `prefers-reduced-motion` → no emptying animation, static count. The ring
 * empties 100%→0% and the color accelerates warning→error in the last ~25%
 * (urgency reinforcement, not decoration). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-offer-timer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-offer-timer"
      [class.jx-offer-timer--attention]="phase() === 'attention'"
      [class.jx-offer-timer--urgent]="phase() === 'urgent'"
    >
      <span
        class="jx-offer-timer__ring"
        [style.--timer-fraction]="fraction()"
        aria-hidden="true"
      ></span>
      <span class="jx-offer-timer__text">
        <span aria-hidden="true">⏱</span>
        <span class="jx-offer-timer__seconds">{{ remaining() }}s</span>
      </span>
      <span class="jx-sr-only" aria-live="polite">{{ liveLabel() }}</span>
    </span>
  `,
  styleUrl: './offer-timer.component.scss',
})
export class OfferTimerComponent implements OnDestroy {
  private readonly _total = signal(20);
  private readonly _remaining = signal(20);
  private readonly _liveLabel = signal('');
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private lastMilestone = -1;

  /** Total window in seconds (from the server — config da área). */
  @Input() set ttlTotalS(value: number) {
    this._total.set(Math.max(1, value));
  }

  /** Authoritative remaining seconds (server re-sync — ADR-104). Starts the tick. */
  @Input() set ttlRemainingS(value: number) {
    this._remaining.set(Math.max(0, value));
    this.announceMilestone(this._remaining(), true);
    this.startTick();
  }

  protected readonly remaining = computed(() => this._remaining());
  protected readonly liveLabel = computed(() => this._liveLabel());

  /** The emptying fraction (1 → 0) for the ring. */
  protected readonly fraction = computed(() => {
    const total = this._total();
    return total > 0 ? this._remaining() / total : 0;
  });

  /** Urgency phase from the remaining fraction (UI-SPEC §4.2). */
  protected readonly phase = computed<TimerPhase>(() => {
    const f = this.fraction();
    if (f <= 0.25) return 'urgent';
    if (f <= 0.5) return 'attention';
    return 'calm';
  });

  private startTick(): void {
    this.stopTick();
    // Cosmetic local tick; the server re-sync corrects any drift (ADR-104).
    this.intervalId = setInterval(() => {
      const next = Math.max(0, this._remaining() - 1);
      this._remaining.set(next);
      this.announceMilestone(next, false);
      if (next <= 0) {
        this.stopTick();
      }
    }, 1000);
  }

  private stopTick(): void {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  /** Announce at milestones only (open / 10s / 5s / expired) — not every second. */
  private announceMilestone(seconds: number, isOpen: boolean): void {
    let milestone = -1;
    if (seconds <= 0) milestone = 0;
    else if (seconds <= 5) milestone = 5;
    else if (seconds <= 10) milestone = 10;
    else if (isOpen) milestone = 999; // the opening announcement

    if (milestone === this.lastMilestone && !isOpen) {
      return;
    }
    this.lastMilestone = milestone;
    if (seconds <= 0) {
      this._liveLabel.set('Tempo esgotado.');
    } else {
      this._liveLabel.set(`${seconds} segundos para decidir.`);
    }
  }

  ngOnDestroy(): void {
    this.stopTick();
  }
}
