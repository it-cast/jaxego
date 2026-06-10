import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { EmptyStateComponent } from '../../../shared/state/empty-state.component';
import { LoadingSkeletonComponent } from '../../../shared/state/loading-skeleton.component';

/** A row in the KYC review queue (UI-SPEC §5.1). */
export interface KycQueueRow {
  courierId: string; // "cou_…" (mono)
  courierName: string;
  level: 'simples' | 'completa';
  approvedCount: number;
  totalCount: number;
  /** Hours the courier has been waiting (drives the ≥48h escalation flag). */
  waitingHours: number;
  /** Optional area name (platform-admin cross-area consolidated view). */
  areaName?: string;
}

/**
 * jx-kyc-queue-table — the area admin's KYC queue (UI-SPEC §5.1 / data-tables +
 * saas-dashboard). Semantic <table> with <th scope>, sortable by "waiting",
 * aria-sort. A courier waiting ≥48h carries the "Atrasada" flag (text + icon,
 * never colour alone — E5). Empty = jx-empty-state (cause+context, no false CTA);
 * loading = skeleton rows. CPF is never shown here (only the cou_ id, mono).
 *
 * Tokens: only semantic vars; no hex.
 */
@Component({
  selector: 'jx-kyc-queue-table',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [EmptyStateComponent, LoadingSkeletonComponent],
  template: `
    @if (loading) {
      <div class="jx-kyc-queue__loading" aria-busy="true">
        @for (n of skeletonRows; track n) {
          <jx-loading-skeleton variant="line" />
        }
      </div>
    } @else if (rows.length === 0) {
      <jx-empty-state
        icon="◷"
        title="Nenhum entregador na fila."
        message="Quando alguém se cadastrar na sua cidade, aparece aqui para revisão."
      />
    } @else {
      <table class="jx-kyc-queue">
        <thead>
          <tr>
            <th scope="col">Entregador</th>
            <th scope="col">Nível</th>
            <th scope="col">Itens</th>
            <th scope="col" [attr.aria-sort]="ariaSort">
              <button type="button" class="jx-kyc-queue__sort" (click)="toggleSort()">
                Esperando há
                <span aria-hidden="true">{{ sortDir === 'desc' ? '▾' : '▴' }}</span>
              </button>
            </th>
            @if (showArea) {
              <th scope="col">Área</th>
            }
            <th scope="col"><span class="jx-sr-only">Ação</span></th>
          </tr>
        </thead>
        <tbody>
          @for (row of sortedRows; track row.courierId) {
            <tr [class.jx-kyc-queue__row--late]="isLate(row)">
              <td>
                <span class="jx-kyc-queue__name">{{ row.courierName }}</span>
                <span class="jx-kyc-queue__id">{{ row.courierId }}</span>
              </td>
              <td>
                <span class="jx-kyc-queue__level">{{ levelLabel(row.level) }}</span>
              </td>
              <td class="jx-kyc-queue__mono">
                {{ row.approvedCount }} de {{ row.totalCount }} aprovados
              </td>
              <td class="jx-kyc-queue__mono">
                {{ waitingLabel(row) }}
                @if (isLate(row)) {
                  <span class="jx-kyc-queue__late" role="status">
                    <span aria-hidden="true">⚑</span> Atrasada
                  </span>
                }
              </td>
              @if (showArea) {
                <td>{{ row.areaName }}</td>
              }
              <td>
                <button
                  type="button"
                  class="jx-kyc-queue__review"
                  (click)="review.emit(row.courierId)"
                >
                  Revisar →
                </button>
              </td>
            </tr>
          }
        </tbody>
      </table>
    }
  `,
  styleUrl: './queue-table.component.scss',
})
export class KycQueueTableComponent {
  @Input() rows: KycQueueRow[] = [];
  @Input() loading = false;
  /** Show the "Área" column (platform-admin cross-area consolidated view). */
  @Input() showArea = false;
  @Output() review = new EventEmitter<string>();

  protected readonly skeletonRows = [0, 1, 2, 3, 4];
  protected sortDir: 'asc' | 'desc' = 'desc';

  protected get ariaSort(): 'ascending' | 'descending' {
    return this.sortDir === 'desc' ? 'descending' : 'ascending';
  }

  protected get sortedRows(): KycQueueRow[] {
    const factor = this.sortDir === 'desc' ? -1 : 1;
    return [...this.rows].sort((a, b) => (a.waitingHours - b.waitingHours) * factor);
  }

  protected toggleSort(): void {
    this.sortDir = this.sortDir === 'desc' ? 'asc' : 'desc';
  }

  protected isLate(row: KycQueueRow): boolean {
    return row.waitingHours >= 48;
  }

  protected levelLabel(level: 'simples' | 'completa'): string {
    return level === 'completa' ? 'Completa' : 'Simples';
  }

  protected waitingLabel(row: KycQueueRow): string {
    if (row.waitingHours < 24) {
      return `${row.waitingHours}h`;
    }
    const days = Math.floor(row.waitingHours / 24);
    return `${days}d`;
  }
}
