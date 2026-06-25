import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStar } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'jx-favorite-row',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FaIconComponent],
  template: `
    <li class="jx-favorite-row">
      <span class="jx-favorite-row__pos" aria-hidden="true">{{ position }}·</span>
      <span class="jx-favorite-row__name">{{ name }}</span>
      <span class="jx-favorite-row__rating">
        <fa-icon [icon]="iconStar" class="jx-favorite-row__star" aria-hidden="true" />
        {{ avgStars > 0 ? avgStars : 'Sem avaliação' }}
      </span>
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
  protected readonly iconStar = faStar;

  @Input({ required: true }) position = 1;
  @Input({ required: true }) name = '';
  @Input() avgStars = 0;
  @Input() canMoveUp = true;
  @Input() canMoveDown = true;

  @Output() moveUp = new EventEmitter<void>();
  @Output() moveDown = new EventEmitter<void>();
  @Output() remove = new EventEmitter<void>();
}
