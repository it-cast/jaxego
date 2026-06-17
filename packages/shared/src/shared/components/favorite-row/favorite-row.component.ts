import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { ScoreChipComponent, type ScoreLevel } from '../score-chip/score-chip.component';

/**
 * jx-favorite-row — a favorite courier row (tela 15, UI-SPEC §5.1). Shows the
 * cascade position (mono) · name · jx-score-chip · stats (mono) and the actions:
 * move ↑ / move ↓ (reorder the cascade priority — D-01, keyboard ≥44px, NOT drag)
 * and remove. The first/last row disables the respective arrow (aria-disabled).
 * Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-favorite-row',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ScoreChipComponent],
  template: `
    <li class="jx-favorite-row">
      <span class="jx-favorite-row__pos" aria-hidden="true">{{ position }}·</span>
      <span class="jx-favorite-row__name">{{ name }}</span>
      <jx-score-chip [level]="scoreLevel" [value]="scoreValue" />
      @if (stats) {
        <span class="jx-favorite-row__stats">{{ stats }}</span>
      }
      <span class="jx-favorite-row__actions">
        <button
          type="button"
          class="jx-favorite-row__move"
          [disabled]="!canMoveUp"
          [attr.aria-disabled]="!canMoveUp"
          [attr.aria-label]="'Subir ' + name + ' na prioridade'"
          (click)="moveUp.emit()"
        >
          ↑
        </button>
        <button
          type="button"
          class="jx-favorite-row__move"
          [disabled]="!canMoveDown"
          [attr.aria-disabled]="!canMoveDown"
          [attr.aria-label]="'Descer ' + name + ' na prioridade'"
          (click)="moveDown.emit()"
        >
          ↓
        </button>
        <button
          type="button"
          class="jx-favorite-row__remove"
          [attr.aria-label]="'Remover ' + name + ' dos favoritos'"
          (click)="remove.emit()"
        >
          Remover
        </button>
      </span>
    </li>
  `,
  styleUrl: './favorite-row.component.scss',
})
export class FavoriteRowComponent {
  /** Cascade position (1-based, mono). */
  @Input({ required: true }) position = 1;
  @Input({ required: true }) name = '';
  @Input() scoreLevel: ScoreLevel = 'probation';
  @Input() scoreValue: number | null = null;
  /** Stats line (e.g. "142 entregas pra você · 96% no prazo"). */
  @Input() stats: string | null = null;
  @Input() canMoveUp = true;
  @Input() canMoveDown = true;

  @Output() moveUp = new EventEmitter<void>();
  @Output() moveDown = new EventEmitter<void>();
  @Output() remove = new EventEmitter<void>();
}
