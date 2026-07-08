import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

/**
 * jx-empty-state — legitimate "no data" state (not an error). UI-SPEC §4.1.
 * Copy rule (empty-states-polish): cause + action, never "Lista vazia".
 * role="status" so it announces without interrupting.
 */
@Component({
  selector: 'jx-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-empty" role="status">
      @if (imgSrc) {
        <img [src]="imgSrc" class="jx-empty__img" aria-hidden="true" />
      } @else if (icon) {
        <span class="jx-empty__icon" aria-hidden="true">{{ icon }}</span>
      }
      <h2 class="jx-empty__title">{{ title }}</h2>
      @if (message) {
        <p class="jx-empty__message">{{ message }}</p>
      }
      @if (ctaLabel) {
        <button type="button" class="jx-empty__cta" (click)="cta.emit()">
          {{ ctaLabel }}
        </button>
      }
    </div>
  `,
  styleUrl: './empty-state.component.scss',
})
export class EmptyStateComponent {
  @Input({ required: true }) title = '';
  @Input() message?: string;
  @Input() ctaLabel?: string;
  @Input() icon?: string;
  @Input() imgSrc?: string;
  @Output() cta = new EventEmitter<void>();
}
