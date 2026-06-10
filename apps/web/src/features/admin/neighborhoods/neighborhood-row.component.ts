import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import type { Neighborhood } from './neighborhoods.service';

/**
 * jx-neighborhood-row — a governed catalog row (UI-SPEC §3.2). Renders the cells
 * for one neighborhood inside jx-data-table: name (+ "informal" selo), polygon
 * status badge (text + icon + colour — never colour alone), and the remove
 * action (outline, error). Tokens only.
 */
@Component({
  selector: 'jx-neighborhood-row',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display: contents' },
  template: `
    <td>
      <span class="jx-nbhd-row__name">{{ item.name }}</span>
      @if (item.is_informal) {
        <span class="jx-nbhd-row__informal">· informal</span>
      }
    </td>
    <td>
      <span
        class="jx-nbhd-row__badge"
        [class.jx-nbhd-row__badge--defined]="item.polygon_status === 'defined'"
        [class.jx-nbhd-row__badge--byname]="item.polygon_status === 'by_name'"
      >
        <span aria-hidden="true">{{
          item.polygon_status === 'defined' ? '◆' : '○'
        }}</span>
        {{ item.polygon_status === 'defined' ? 'Polígono definido' : 'Por nome' }}
      </span>
    </td>
    <td class="jx-nbhd-row__actions">
      <button
        type="button"
        class="jx-nbhd-row__remove"
        (click)="remove.emit(item.id)"
      >
        Remover
      </button>
    </td>
  `,
  styleUrl: './neighborhood-row.component.scss',
})
export class NeighborhoodRowComponent {
  @Input({ required: true }) item!: Neighborhood;
  @Output() remove = new EventEmitter<number>();
}
