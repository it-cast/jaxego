import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';

export type TrackingState =
  | 'CRIADA'
  | 'ACEITA'
  | 'COLETADA'
  | 'ENTREGUE'
  | 'RECUSADA_NO_DESTINO'
  | 'CANCELADA'
  | 'FINALIZADA';

export interface TimelineEntry {
  state: string;
  at: string | null;
}

interface Step {
  state: TrackingState;
  label: string;
  /** 'done' (past), 'current' (now), 'future' (not yet). */
  status: 'done' | 'current' | 'future';
  at: string | null;
}

/** The happy-path order of the visible milestones. */
const HAPPY_PATH: TrackingState[] = ['CRIADA', 'ACEITA', 'COLETADA', 'ENTREGUE', 'FINALIZADA'];

const LABELS: Record<TrackingState, string> = {
  CRIADA: 'Pedido recebido',
  ACEITA: 'Entregador a caminho da coleta',
  COLETADA: 'Pedido coletado, a caminho de você',
  ENTREGUE: 'Pedido entregue',
  FINALIZADA: 'Concluído',
  RECUSADA_NO_DESTINO: 'Não foi possível entregar',
  CANCELADA: 'Pedido cancelado',
};

/**
 * jx-tracking-timeline — the vertical state timeline (UI-SPEC §11). Shared by the
 * store detail (tela 13) and the public tracker (tela 26); it is the TEXTUAL
 * ALTERNATIVE to the map and the LCP of the tracker.
 *
 * Steps are distinguished by SHAPE (filled / ring / hollow) + LABEL, never colour
 * alone (accessibility-pro). The current step gets `aria-live="polite"` so a state
 * change is announced. Horários in mono. Persimmon (--brand) marks only the current
 * step (ui-ux-pro-max — accent reserved). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-tracking-timeline',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ol class="jx-timeline" aria-label="Andamento da entrega">
      @for (step of steps(); track step.state) {
        <li
          class="jx-timeline__step"
          [class.jx-timeline__step--done]="step.status === 'done'"
          [class.jx-timeline__step--current]="step.status === 'current'"
          [attr.aria-current]="step.status === 'current' ? 'step' : null"
        >
          <span class="jx-timeline__marker" aria-hidden="true">
            {{ step.status === 'done' ? '●' : step.status === 'current' ? '◉' : '○' }}
          </span>
          <span class="jx-timeline__body" [attr.aria-live]="step.status === 'current' ? 'polite' : null">
            <span class="jx-timeline__label">{{ step.label }}</span>
            @if (step.at) {
              <time class="jx-timeline__time">{{ formatTime(step.at) }}</time>
            }
          </span>
        </li>
      }
    </ol>
  `,
  styleUrl: './tracking-timeline.component.scss',
})
export class TrackingTimelineComponent {
  private readonly _state = signal<TrackingState>('CRIADA');
  private readonly _entries = signal<TimelineEntry[]>([]);

  @Input({ required: true })
  set state(value: TrackingState) {
    this._state.set(value);
  }

  /** The append-only history milestones (state + ISO timestamp). */
  @Input()
  set entries(value: TimelineEntry[]) {
    this._entries.set(value ?? []);
  }

  protected readonly steps = computed<Step[]>(() => {
    const current = this._state();
    const byState = new Map(this._entries().map((e) => [e.state, e.at]));

    // Diverted terminal states (refused/cancelled) replace the tail.
    if (current === 'CANCELADA' || current === 'RECUSADA_NO_DESTINO') {
      const reached = HAPPY_PATH.filter((s) => byState.has(s) && s !== 'ENTREGUE' && s !== 'FINALIZADA');
      return [
        ...reached.map((s) => this.step(s, 'done', byState.get(s) ?? null)),
        this.step(current, 'current', byState.get(current) ?? null),
      ];
    }

    const idx = HAPPY_PATH.indexOf(current);
    return HAPPY_PATH.map((s, i) => {
      const status: Step['status'] = i < idx ? 'done' : i === idx ? 'current' : 'future';
      return this.step(s, status, byState.get(s) ?? null);
    });
  });

  private step(state: TrackingState, status: Step['status'], at: string | null): Step {
    return { state, label: LABELS[state], status, at };
  }

  protected formatTime(iso: string): string {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }
}
