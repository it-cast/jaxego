import {
  ChangeDetectionStrategy,
  Component,
  Input,
  computed,
  signal,
} from '@angular/core';

/**
 * One explainable score component — mirrors the backend `ScoreComponentRead`
 * (raw value 0..1, weight 0..1, contribution to the total 0..100).
 */
export interface ScoreComponent {
  component: string;
  raw: number;
  weight: number;
  contribution: number;
}

/** pt-BR labels for the known score components (UI-SPEC §copy, sem jargão). */
const COMPONENT_LABELS: Record<string, string> = {
  acceptance: 'Taxa de aceite',
  acceptance_rate: 'Taxa de aceite',
  punctuality: 'Pontualidade',
  proof_ok: 'Comprovação ok',
  low_cancellation: 'Baixo cancelamento',
  ratings: 'Avaliações das lojas',
};

/**
 * jx-score-breakdown — the EXPLAINABLE score table (UI-SPEC §Score, ADR-013).
 *
 * Transparency is a requirement, not decoration: the admin sees each component
 * with its raw value, weight and contribution to the total — not just the final
 * note. Renders a semantic `<table>` with `<th scope>` headers, keyboard-reachable
 * and AA in both themes. The score is informative only in M1 (no financial weight
 * — ADR-013), made explicit by an inline note. Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-score-breakdown',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-score-breakdown">
      <table>
        <caption class="jx-sr-only">{{ caption }}</caption>
        <thead>
          <tr>
            <th scope="col">Componente</th>
            <th scope="col" class="jx-score-breakdown__num">Valor</th>
            <th scope="col" class="jx-score-breakdown__num">Peso</th>
            <th scope="col" class="jx-score-breakdown__num">Contribuição</th>
          </tr>
        </thead>
        <tbody>
          @for (row of rows(); track row.component) {
            <tr>
              <th scope="row">{{ labelFor(row.component) }}</th>
              <td class="jx-score-breakdown__num">{{ pct(row.raw) }}</td>
              <td class="jx-score-breakdown__num">{{ pct(row.weight) }}</td>
              <td class="jx-score-breakdown__num jx-score-breakdown__contrib">
                {{ points(row.contribution) }}
              </td>
            </tr>
          }
        </tbody>
        @if (hasTotal()) {
          <tfoot>
            <tr>
              <th scope="row">Total</th>
              <td></td>
              <td></td>
              <td class="jx-score-breakdown__num jx-score-breakdown__total">
                {{ points(totalValue()!) }}
              </td>
            </tr>
          </tfoot>
        }
      </table>
      <p class="jx-score-breakdown__note">
        O score é informativo no piloto — não altera ofertas nem valores.
      </p>
    </div>
  `,
  styleUrl: './score-breakdown.component.scss',
})
export class ScoreBreakdownComponent {
  private readonly _components = signal<ScoreComponent[]>([]);
  private readonly _total = signal<number | null>(null);

  /** The explainable component lines (from the latest snapshot). */
  @Input({ required: true })
  set components(value: ScoreComponent[] | null | undefined) {
    this._components.set(value ?? []);
  }

  /** Optional total score (renders a Total footer row). */
  @Input()
  set total(value: number | null) {
    this._total.set(value);
  }
  get total(): number | null {
    return this._total();
  }

  /** Accessible table caption (visually hidden). */
  @Input() caption = 'Composição do score por componente';

  protected readonly rows = computed(() => this._components());
  protected readonly totalValue = computed(() => this._total());
  protected readonly hasTotal = computed(() => this._total() !== null);

  protected labelFor(component: string): string {
    return COMPONENT_LABELS[component] ?? component;
  }

  /** A 0..1 ratio rendered as a pt-BR percentage. */
  protected pct(ratio: number): string {
    return `${Math.round(ratio * 100)}%`;
  }

  /** A 0..100 points value in mono, pt-BR comma decimal. */
  protected points(value: number): string {
    return Number.isInteger(value)
      ? String(value)
      : value.toLocaleString('pt-BR', {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        });
  }
}
