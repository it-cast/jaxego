import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { maskBrl } from '@jaxego/shared/util/money';

/** One neighborhood row in the coverage list (UI-SPEC §4). */
export interface CoverageItem {
  neighborhoodId: number;
  name: string;
  /** The courier serves this neighborhood. */
  covered: boolean;
  /** Excluded — vetoes coverage at both points (RN-003). */
  excluded: boolean;
  /** Masked price (mode 'neighborhood' only). */
  price: string;
  /** Inline price error (below floor) — cites the floor. */
  priceError?: string | null;
}

/**
 * jx-coverage-list — the mobile coverage rows (UI-SPEC §4). Each row: a ≥44px
 * touch target to toggle "atendo", the neighborhood name, an "Excluir" toggle
 * (selo "Excluído" that prevails over coverage), and a compact masked price input
 * (mode 'neighborhood'). A non-covered row disables the price. Tokens only.
 */
@Component({
  selector: 'jx-coverage-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ul class="jx-coverage-list">
      @for (item of items; track item.neighborhoodId) {
        <li
          class="jx-coverage-list__row"
          [class.jx-coverage-list__row--excluded]="item.excluded"
        >
          <label class="jx-coverage-list__check">
            <input
              type="checkbox"
              [checked]="item.covered"
              [disabled]="item.excluded"
              (change)="toggleCovered(item)"
            />
            <span class="jx-coverage-list__name">{{ item.name }}</span>
            @if (item.excluded) {
              <span class="jx-coverage-list__badge" role="status">
                <span aria-hidden="true">⊘</span> Excluído
              </span>
            }
          </label>

          @if (showPrice) {
            <div class="jx-coverage-list__price">
              <input
                class="jx-coverage-list__price-input"
                inputmode="decimal"
                placeholder="R$ 0,00"
                [value]="item.price"
                [disabled]="!item.covered || item.excluded"
                [attr.aria-label]="'Preço para ' + item.name"
                [attr.aria-invalid]="item.priceError ? 'true' : null"
                (input)="onPrice(item, $event)"
                (blur)="priceBlur.emit(item)"
              />
              @if (item.priceError) {
                <p class="jx-coverage-list__price-error" role="alert">
                  {{ item.priceError }}
                </p>
              }
            </div>
          }

          <button
            type="button"
            class="jx-coverage-list__exclude"
            (click)="toggleExcluded(item)"
          >
            {{ item.excluded ? 'Reincluir' : 'Excluir' }}
          </button>
        </li>
      }
    </ul>
  `,
  styleUrl: './coverage-list.component.scss',
})
export class CoverageListComponent {
  @Input() items: CoverageItem[] = [];
  /** Show the per-neighborhood price input (mode 'neighborhood'). */
  @Input() showPrice = true;
  @Output() itemsChange = new EventEmitter<CoverageItem[]>();
  @Output() priceBlur = new EventEmitter<CoverageItem>();

  protected toggleCovered(item: CoverageItem): void {
    item.covered = !item.covered;
    this.itemsChange.emit(this.items);
  }

  protected toggleExcluded(item: CoverageItem): void {
    item.excluded = !item.excluded;
    if (item.excluded) {
      item.covered = false;
    }
    this.itemsChange.emit(this.items);
  }

  protected onPrice(item: CoverageItem, event: Event): void {
    item.price = maskBrl((event.target as HTMLInputElement).value);
    this.itemsChange.emit(this.items);
  }
}
