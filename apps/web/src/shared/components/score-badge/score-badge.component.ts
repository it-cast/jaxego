import {
  ChangeDetectionStrategy,
  Component,
  Input,
  computed,
  signal,
} from '@angular/core';

/** The 5 score levels (ADR-013 / UI-SPEC §Score) — derived from color.score_level. */
export type ScoreLevel = 'probation' | 'bronze' | 'prata' | 'ouro' | 'diamante';

interface ScoreLevelMeta {
  /** CSS custom property name for the vivid score color (--score-*). */
  cssVar: string;
  /** pt-BR label — the meaning is carried by TEXT (never color-only — a11y). */
  label: string;
}

const LEVEL_META: Record<ScoreLevel, ScoreLevelMeta> = {
  probation: { cssVar: '--score-probation', label: 'Em avaliação' },
  bronze: { cssVar: '--score-bronze', label: 'Bronze' },
  prata: { cssVar: '--score-prata', label: 'Prata' },
  ouro: { cssVar: '--score-ouro', label: 'Ouro' },
  diamante: { cssVar: '--score-diamante', label: 'Diamante' },
};

/**
 * jx-score-badge — the score-level badge for DETAIL surfaces (UI-SPEC §Score,
 * ADR-013). Renders the level NAME + COLOR + (optional) mono VALUE — never
 * color-only (a11y / daltonismo). Each of the 5 levels maps 1:1 to a `--score-*`
 * semantic var (derived mechanically from `color.score_level`, same pattern as
 * `jx-score-chip` and `jx-state-badge`).
 *
 * The chip (`jx-score-chip`) is the inline, table-cell vocabulary; the badge is
 * the larger detail-screen badge (telas 19/20/24) with the value emphasised.
 * Score is EXHIBITED only in M1 (no financial weight — ADR-013). Tokens only —
 * no hex (Gate 2).
 */
@Component({
  selector: 'jx-score-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-score-badge"
      [class.jx-score-badge--lg]="size === 'lg'"
      [style.--score-color]="'var(' + meta().cssVar + ')'"
      [attr.aria-label]="ariaLabel()"
    >
      @if (hasValue()) {
        <span class="jx-score-badge__value">{{ valueLabel() }}</span>
      }
      <span class="jx-score-badge__level">{{ meta().label }}</span>
    </span>
  `,
  styleUrl: './score-badge.component.scss',
})
export class ScoreBadgeComponent {
  private readonly _level = signal<ScoreLevel>('probation');
  private readonly _value = signal<number | null>(null);

  /** The score level (drives color + label). */
  @Input({ required: true })
  set level(value: ScoreLevel) {
    this._level.set(value);
  }

  /** The numeric score (optional). Rendered in mono with pt-BR comma decimal. */
  @Input()
  set value(value: number | null) {
    this._value.set(value);
  }

  /** Visual size — `md` (default) for cells/lists, `lg` for detail headers. */
  @Input() size: 'md' | 'lg' = 'md';

  protected readonly meta = computed(() => LEVEL_META[this._level()]);
  protected readonly hasValue = computed(() => this._value() !== null);

  protected readonly valueLabel = computed(() => {
    const v = this._value();
    if (v === null) {
      return '';
    }
    // pt-BR comma decimal; integers shown without a decimal part.
    return Number.isInteger(v)
      ? String(v)
      : v.toLocaleString('pt-BR', {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        });
  });

  protected readonly ariaLabel = computed(() => {
    const v = this._value();
    const lvl = this.meta().label;
    return v === null
      ? `Nível ${lvl}`
      : `Score ${this.valueLabel()}, nível ${lvl}`;
  });
}
