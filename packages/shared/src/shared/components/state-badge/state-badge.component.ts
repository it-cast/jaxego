import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';

/** The 8 canonical delivery states (RN-019 / D-03). */
export type DeliveryState =
  | 'AGENDADA'
  | 'CRIADA'
  | 'ACEITA'
  | 'COLETADA'
  | 'ENTREGUE'
  | 'RECUSADA_NO_DESTINO'
  | 'CANCELADA'
  | 'FINALIZADA';

/** Which vocabulary to use for the label (UI-SPEC §3.1). */
export type StateBadgeVariant = 'list' | 'dashboard';

interface StateMeta {
  /** CSS custom property name for the vivid color. */
  cssVar: string;
  /** Glyph (aria-hidden) — meaning is carried by the TEXT (a11y, never color-only). */
  icon: string;
  /** Label in the store-facing list vocabulary. */
  list: string;
  /** Label in the dashboard "journey" vocabulary. */
  dashboard: string;
}

/**
 * jx-state-badge — the SINGLE source of the delivery-state visual vocabulary
 * (UI-SPEC §3, RN-019). Renders TEXT + ICON + COLOR (never color-only — a11y).
 * Each of the 7 states maps 1:1 to a `--state-*` semantic var (derived from
 * `color.delivery_state`). `[variant]` switches ONLY the label (list vs dashboard
 * journey), keeping color + icon + canonical code identical.
 *
 * Only CRIADA and CANCELADA are reachable in Phase 7 (the delivery is born CRIADA;
 * the store may cancel pre-acceptance); the other 5 are defined here so Phases 8/9
 * need no redesign. Tokens: only semantic `--state-*` vars + neutral surface — no
 * hex (Gate 2).
 */
@Component({
  selector: 'jx-state-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-state-badge"
      [style.--state-color]="'var(' + meta().cssVar + ')'"
      [class.jx-state-badge--dashboard]="variant === 'dashboard'"
    >
      <span class="jx-state-badge__label">{{ label() }}</span>
    </span>
  `,
  styleUrl: './state-badge.component.scss',
})
export class StateBadgeComponent {
  private readonly _state = signal<DeliveryState>('CRIADA');
  private readonly _variant = signal<StateBadgeVariant>('list');

  @Input({ required: true })
  set state(value: DeliveryState) {
    this._state.set(value);
  }
  get state(): DeliveryState {
    return this._state();
  }

  @Input()
  set variant(value: StateBadgeVariant) {
    this._variant.set(value);
  }
  get variant(): StateBadgeVariant {
    return this._variant();
  }

  protected readonly META: Record<DeliveryState, StateMeta> = {
    AGENDADA: { cssVar: '--state-agendada', icon: '⏰', list: 'Agendada', dashboard: 'Agendada' },
    CRIADA: { cssVar: '--state-criada', icon: '◷', list: 'Procurando', dashboard: 'Procurando' },
    ACEITA: { cssVar: '--state-aceita', icon: '✓', list: 'Aceita', dashboard: 'Indo coletar' },
    COLETADA: {
      cssVar: '--state-coletada',
      icon: '→',
      list: 'A caminho',
      dashboard: 'A caminho',
    },
    ENTREGUE: { cssVar: '--state-entregue', icon: '⤓', list: 'Entregue', dashboard: 'Entregue' },
    RECUSADA_NO_DESTINO: {
      cssVar: '--state-recusada',
      icon: '⊘',
      list: 'Recusada no destino',
      dashboard: 'Recusada',
    },
    CANCELADA: {
      cssVar: '--state-cancelada',
      icon: '×',
      list: 'Cancelada',
      dashboard: 'Cancelada',
    },
    FINALIZADA: {
      cssVar: '--state-finalizada',
      icon: '✓✓',
      list: 'Finalizada',
      dashboard: 'Finalizada',
    },
  };

  protected readonly meta = computed(() => this.META[this._state()]);
  protected readonly label = computed(() =>
    this._variant() === 'dashboard' ? this.meta().dashboard : this.meta().list,
  );
}
