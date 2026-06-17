import {
  ChangeDetectionStrategy,
  Component,
  Input,
  computed,
  signal,
} from '@angular/core';

/** The 5 score levels (ADR-013 / UI-SPEC §7.1) — derived from color.score_level. */
export type ScoreLevel = 'probation' | 'bronze' | 'prata' | 'ouro' | 'diamante';

interface ScoreMeta {
  /** CSS custom property name for the vivid color (--score-*). */
  cssVar: string;
  /** pt-BR label — the meaning is carried by TEXT (never color-only — a11y). */
  label: string;
}

const SCORE_META: Record<ScoreLevel, ScoreMeta> = {
  probation: { cssVar: '--score-probation', label: 'em avaliação' },
  bronze: { cssVar: '--score-bronze', label: 'bronze' },
  prata: { cssVar: '--score-prata', label: 'prata' },
  ouro: { cssVar: '--score-ouro', label: 'ouro' },
  diamante: { cssVar: '--score-diamante', label: 'diamante' },
};

/**
 * jx-score-chip — the score-level visual vocabulary (UI-SPEC §7, ADR-013).
 * Renders GLYPH (aria-hidden) + mono VALUE + level TEXT + COLOR — never
 * color-only (a11y). Each of the 5 levels maps 1:1 to a `--score-*` semantic var
 * (derived mechanically from `color.score_level`, same pattern as `--state-*`).
 * Score is EXHIBITED only in M1 (no financial weight — ADR-013). Tokens only — no
 * hex (Gate 2).
 */
@Component({
  selector: 'jx-score-chip',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-score-chip"
      [style.--score-color]="'var(' + meta().cssVar + ')'"
      [attr.aria-label]="ariaLabel()"
    >
      <span class="jx-score-chip__glyph" aria-hidden="true">★</span>
      @if (hasValue()) {
        <span class="jx-score-chip__value">{{ valueLabel() }}</span>
      }
      <span class="jx-score-chip__level">{{ meta().label }}</span>
    </span>
  `,
  styleUrl: './score-chip.component.scss',
})
export class ScoreChipComponent {
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

  protected readonly meta = computed(() => SCORE_META[this._level()]);
  protected readonly hasValue = computed(() => this._value() !== null);

  protected readonly valueLabel = computed(() => {
    const v = this._value();
    if (v === null) {
      return '';
    }
    // pt-BR comma decimal; integers shown without a decimal part.
    return Number.isInteger(v)
      ? String(v)
      : v.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  });

  protected readonly ariaLabel = computed(() => {
    const v = this._value();
    const lvl = this.meta().label;
    return v === null ? `Nível ${lvl}` : `Score ${this.valueLabel()}, nível ${lvl}`;
  });
}
