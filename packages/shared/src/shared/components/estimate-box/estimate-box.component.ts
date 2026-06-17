import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { LoadingSkeletonComponent } from '../../state/loading-skeleton.component';
import { formatBrl } from '../../util/money';

/**
 * jx-estimate-box — the freight estimate (median, RN-030) + platform fee, shown
 * BEFORE confirming (UI-SPEC §2.7). `role="status"` `aria-live="polite"` so a
 * recalculation is announced. Three variants:
 *   - loading: a skeleton inside the box (aria-busy).
 *   - range: "R$ X–Y" + fee + "(N entregadores online)".
 *   - empty (E2 / D-06): "Sem estimativa agora" — non-blocking, the store decides.
 *
 * Values are integer cents from the API (formatted with formatBrl) — NOTHING is
 * hardcoded. Tokens only (brand-wash surface) — no hex (Gate 2).
 */
@Component({
  selector: 'jx-estimate-box',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LoadingSkeletonComponent],
  template: `
    <div
      class="jx-estimate-box"
      role="status"
      aria-live="polite"
      [attr.aria-busy]="loading ? 'true' : null"
    >
      <div class="jx-estimate-box__label">
        <span>Frete estimado</span>
        @if (!loading && estimateMinCents !== null) {
          <small>({{ courierCount }} {{ courierCount === 1 ? 'entregador' : 'entregadores' }} online)</small>
        }
      </div>

      @if (loading) {
        <jx-loading-skeleton variant="line" />
      } @else if (estimateMinCents === null) {
        <div class="jx-estimate-box__empty">Sem estimativa agora</div>
      } @else {
        <div class="jx-estimate-box__value">
          <span class="jx-estimate-box__amount">{{ range() }}</span>
          @if (feeCents !== null && feeCents > 0) {
            <span class="jx-estimate-box__fee">+ taxa {{ fee() }}</span>
          }
        </div>
      }
    </div>
    <p class="jx-estimate-box__disclaimer">
      Estimativa pela mediana de quem está online. O valor final é a tabela de quem aceitar.
    </p>
  `,
  styleUrl: './estimate-box.component.scss',
})
export class EstimateBoxComponent {
  /** Estimate range in integer cents (null = no estimate / E2). */
  @Input() estimateMinCents: number | null = null;
  @Input() estimateMaxCents: number | null = null;
  @Input() feeCents: number | null = null;
  @Input() courierCount = 0;
  @Input() loading = false;

  protected range(): string {
    const min = this.estimateMinCents ?? 0;
    const max = this.estimateMaxCents ?? min;
    if (min === max) {
      return formatBrl(min / 100);
    }
    return `${formatBrl(min / 100)}–${formatBrl(max / 100)}`;
  }

  protected fee(): string {
    return formatBrl((this.feeCents ?? 0) / 100);
  }
}
