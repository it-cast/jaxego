import {
  ChangeDetectionStrategy,
  Component,
  ContentChild,
  EventEmitter,
  Input,
  Output,
  TemplateRef,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { EmptyStateComponent } from '../../state/empty-state.component';
import { ErrorStateComponent } from '../../state/error-state.component';
import { LoadingSkeletonComponent } from '../../state/loading-skeleton.component';

/** A column definition for jx-data-table (UI-SPEC §3.1). */
export interface DataTableColumn {
  /** Stable key used to read the cell value and as the sort key. */
  key: string;
  /** Visible column header (overline). */
  label: string;
  /** Whether the column is sortable (renders a real button + aria-sort). */
  sortable?: boolean;
  /** Right-align (numeric/mono data). */
  numeric?: boolean;
}

export type DataTableState = 'loading' | 'empty' | 'error' | 'ready';
type SortDir = 'asc' | 'desc' | 'none';

/**
 * jx-data-table — the governed, accessible table PRIMITIVE (UI-SPEC §3.1).
 *
 * Generalises the Phase 5 KYC queue: a semantic `<table>` in an elevated surface,
 * sticky `<thead>`, `<th scope="col">` overlines, sortable columns via a REAL
 * button + `aria-sort`, optional zebra, hover wash, ≥44px row-action area, and the
 * four states (loading/empty/error/ready) embedded in place of `<tbody>`.
 *
 * Cells are projected: the consumer supplies a `<ng-template #row let-item>` that
 * renders the `<td>`s for one row, plus optional action template. Tokens: only
 * semantic vars — no hex, no new var.
 */
@Component({
  selector: 'jx-data-table',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgTemplateOutlet,
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingSkeletonComponent,
  ],
  template: `
    <div class="jx-data-table" [class.jx-data-table--zebra]="zebra">
      <table>
        <caption [class.jx-sr-only]="captionHidden">{{ caption }}</caption>
        <thead>
          <tr>
            @for (col of columns; track col.key) {
              <th
                scope="col"
                [class.jx-data-table__num]="col.numeric"
                [attr.aria-sort]="col.sortable ? ariaSortFor(col.key) : null"
              >
                @if (col.sortable) {
                  <button
                    type="button"
                    class="jx-data-table__sort"
                    (click)="toggleSort(col.key)"
                  >
                    {{ col.label }}
                    <span aria-hidden="true">{{ sortGlyph(col.key) }}</span>
                  </button>
                } @else {
                  {{ col.label }}
                }
              </th>
            }
            @if (hasActions) {
              <th scope="col"><span class="jx-sr-only">Ações</span></th>
            }
          </tr>
        </thead>

        @if (state === 'ready') {
          <tbody>
            @for (item of rows; track trackBy(item)) {
              <tr>
                <ng-container
                  [ngTemplateOutlet]="rowTemplate"
                  [ngTemplateOutletContext]="{ $implicit: item }"
                />
              </tr>
            }
          </tbody>
        }
      </table>

      @if (state === 'loading') {
        <div class="jx-data-table__state" aria-busy="true">
          @for (n of skeletonRows; track n) {
            <jx-loading-skeleton variant="line" />
          }
        </div>
      } @else if (state === 'empty') {
        <div class="jx-data-table__state">
          <jx-empty-state
            [icon]="emptyIcon"
            [title]="emptyTitle"
            [message]="emptyMessage"
            [ctaLabel]="emptyCtaLabel"
            (cta)="emptyCta.emit()"
          />
        </div>
      } @else if (state === 'error') {
        <div class="jx-data-table__state">
          <jx-error-state
            [message]="errorMessage"
            retryLabel="Tentar de novo"
            (retry)="retry.emit()"
          />
        </div>
      }
    </div>
  `,
  styleUrl: './data-table.component.scss',
})
export class DataTableComponent {
  @Input() columns: DataTableColumn[] = [];
  @Input() rows: unknown[] = [];
  @Input() state: DataTableState = 'ready';
  @Input() caption = '';
  @Input() captionHidden = true;
  @Input() zebra = false;
  @Input() hasActions = false;
  /** Function used to track rows (defaults to identity). */
  @Input() trackBy: (item: unknown) => unknown = (item) => item;

  // Empty-state content.
  @Input() emptyIcon = '◌';
  @Input() emptyTitle = 'Nada por aqui ainda.';
  @Input() emptyMessage?: string;
  @Input() emptyCtaLabel?: string;

  // Error-state content.
  @Input() errorMessage = 'Não foi possível carregar. Tente de novo.';

  @Output() sortChange = new EventEmitter<{ key: string; dir: SortDir }>();
  @Output() retry = new EventEmitter<void>();
  @Output() emptyCta = new EventEmitter<void>();

  @ContentChild('row', { static: false })
  rowTemplate!: TemplateRef<unknown>;

  protected readonly skeletonRows = [0, 1, 2, 3, 4];
  protected sortKey: string | null = null;
  protected sortDir: SortDir = 'none';

  protected ariaSortFor(key: string): 'ascending' | 'descending' | 'none' {
    if (this.sortKey !== key || this.sortDir === 'none') {
      return 'none';
    }
    return this.sortDir === 'asc' ? 'ascending' : 'descending';
  }

  protected sortGlyph(key: string): string {
    if (this.sortKey !== key || this.sortDir === 'none') {
      return '↕';
    }
    return this.sortDir === 'asc' ? '▴' : '▾';
  }

  protected toggleSort(key: string): void {
    if (this.sortKey !== key) {
      this.sortKey = key;
      this.sortDir = 'asc';
    } else {
      this.sortDir =
        this.sortDir === 'asc' ? 'desc' : this.sortDir === 'desc' ? 'none' : 'asc';
      if (this.sortDir === 'none') {
        this.sortKey = null;
      }
    }
    this.sortChange.emit({ key, dir: this.sortDir });
  }
}
