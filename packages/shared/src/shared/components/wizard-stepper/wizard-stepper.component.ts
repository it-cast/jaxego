import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

export interface WizardStep {
  /** Short uppercase label (overline pattern). */
  label: string;
}

/**
 * jx-wizard-stepper — horizontal step indicator (UI-SPEC §2.2).
 *
 * A11y (accessibility-pro): <nav><ol>; current step aria-current="step"; the
 * state is conveyed by check + weight + aria-current, NEVER colour alone.
 * Completed steps are <button>s (go back); future steps are inert. A polite live
 * region announces "Passo N de M" on change. Tokens: only semantic vars (no hex).
 */
@Component({
  selector: 'jx-wizard-stepper',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav class="jx-stepper" aria-label="Etapas do cadastro">
      <ol class="jx-stepper__list">
        @for (step of steps; track $index) {
          <li
            class="jx-stepper__item"
            [class.jx-stepper__item--done]="$index < current"
            [class.jx-stepper__item--current]="$index === current"
            [attr.aria-current]="$index === current ? 'step' : null"
          >
            @if ($index < current) {
              <button
                type="button"
                class="jx-stepper__node"
                (click)="goTo.emit($index)"
                [attr.aria-label]="'Voltar para ' + step.label"
              >
                <span class="jx-stepper__check" aria-hidden="true">✓</span>
              </button>
            } @else {
              <span class="jx-stepper__node" aria-hidden="true">
                {{ $index + 1 }}
              </span>
            }
            <span class="jx-stepper__label">{{ step.label }}</span>
          </li>
        }
      </ol>
      <p class="jx-stepper__status" aria-live="polite">
        Passo {{ current + 1 }} de {{ steps.length }}
      </p>
    </nav>
  `,
  styleUrl: './wizard-stepper.component.scss',
})
export class WizardStepperComponent {
  @Input({ required: true }) steps: WizardStep[] = [];
  /** Zero-based index of the current step. */
  @Input() current = 0;
  @Output() goTo = new EventEmitter<number>();
}
