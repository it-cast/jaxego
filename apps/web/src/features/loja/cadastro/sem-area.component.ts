import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { inject } from '@angular/core';
import { EmptyStateComponent } from '@jaxego/shared/state';
import { FieldComponent } from '@jaxego/shared/components';

/**
 * "Ainda não chegamos aí" empty state (UI-SPEC §5). Reuses jx-empty-state
 * (cause + action) with an interest-capture slot (LGPD consent). Submits to
 * /v1/interest via the parent. role="status"; focus moves to the title on show.
 */
@Component({
  selector: 'jx-sem-area',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, EmptyStateComponent, FieldComponent],
  template: `
    <div class="jx-sem-area" role="status">
      @if (!sent()) {
        <jx-empty-state
          title="Ainda não chegamos na sua cidade."
          message="Deixe seu e-mail e a cidade que avisamos quando o Jaxegô chegar aí."
          icon="📍"
        />
        <form class="jx-sem-area__form" [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <jx-field
            label="Seu e-mail"
            type="email"
            inputmode="email"
            autocomplete="email"
            formControlName="email"
            [error]="emailError()"
          />
          <jx-field
            label="Sua cidade"
            autocomplete="address-level2"
            formControlName="cidade"
          />
          <div class="jx-sem-area__consent">
            <label>
              <input type="checkbox" formControlName="consent" />
              Concordo em receber um aviso quando o Jaxegô chegar na minha cidade.
            </label>
          </div>
          <button type="submit" class="jx-sem-area__cta">Avisar quando chegar</button>
        </form>
      } @else {
        <jx-empty-state
          title="Pronto. Avisaremos você assim que chegarmos."
          icon="✓"
        />
      }
    </div>
  `,
  styleUrl: './sem-area.component.scss',
})
export class SemAreaComponent {
  private readonly fb = inject(FormBuilder);

  @Input() set cidade(value: string) {
    if (value) this.form.controls.cidade.setValue(value);
  }
  @Output() interest = new EventEmitter<{ email: string; cidade: string }>();

  protected readonly sent = signal(false);
  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    cidade: ['', Validators.required],
    consent: [false, Validators.requiredTrue],
  });

  protected emailError(): string | null {
    const c = this.form.controls.email;
    return c.touched && c.invalid ? 'Confira o e-mail para avisarmos você.' : null;
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { email, cidade } = this.form.getRawValue();
    this.interest.emit({ email, cidade });
    this.sent.set(true);
  }
}
