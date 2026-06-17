import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

/**
 * jx-error-state — 4xx/5xx / load failure. UI-SPEC §4.2.
 * Copy rule (error-ux-patterns): what happened + what to do, never "Algo deu
 * errado". role="alert" announces immediately; left border 3px --error.
 */
@Component({
  selector: 'jx-error-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-error" role="alert">
      <span class="jx-error__icon" aria-hidden="true">!</span>
      <p class="jx-error__message">{{ message }}</p>
      @if (retryLabel) {
        <button type="button" class="jx-error__retry" (click)="retry.emit()">
          {{ retryLabel }}
        </button>
      }
    </div>
  `,
  styleUrl: './error-state.component.scss',
})
export class ErrorStateComponent {
  @Input({ required: true }) message = '';
  @Input() retryLabel?: string;
  @Output() retry = new EventEmitter<void>();
}
