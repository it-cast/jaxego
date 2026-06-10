import {
  ChangeDetectionStrategy,
  Component,
  Input,
} from '@angular/core';
import {
  ControlValueAccessor,
  NG_VALUE_ACCESSOR,
} from '@angular/forms';

let _uid = 0;

/**
 * jx-field — input + label + error + mask wrapper (UI-SPEC §3).
 *
 * Encapsulates the BR form pattern: label, masked input, inline error associated
 * by aria-describedby, touch ≥44px, focus ring, error border. Implements
 * ControlValueAccessor so it plugs into Reactive Forms. The mask is applied by
 * the parent (passes the already-masked value); this component renders + a11y.
 *
 * Tokens: only semantic vars (design-tokens-system / dark-mode-theming) — no hex.
 * Mono display for data fields (ui-ux-pro-max) via [mono].
 */
@Component({
  selector: 'jx-field',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    { provide: NG_VALUE_ACCESSOR, useExisting: FieldComponent, multi: true },
  ],
  template: `
    <div class="jx-field">
      <label class="jx-field__label" [for]="id">{{ label }}</label>
      <input
        [id]="id"
        class="jx-field__input"
        [class.jx-field__input--mono]="mono"
        [class.jx-field__input--error]="!!error"
        [type]="type"
        [attr.inputmode]="inputmode"
        [attr.autocomplete]="autocomplete"
        [attr.placeholder]="placeholder"
        [attr.maxlength]="maxlength"
        [attr.enterkeyhint]="enterkeyhint"
        [attr.aria-describedby]="error ? id + '-error' : null"
        [attr.aria-invalid]="error ? 'true' : null"
        [disabled]="disabled"
        [value]="value"
        (input)="onInput($event)"
        (blur)="onTouched()"
      />
      @if (hint && !error) {
        <p class="jx-field__hint">{{ hint }}</p>
      }
      @if (error) {
        <p class="jx-field__error" [id]="id + '-error'">{{ error }}</p>
      }
    </div>
  `,
  styleUrl: './field.component.scss',
})
export class FieldComponent implements ControlValueAccessor {
  @Input({ required: true }) label = '';
  @Input() type = 'text';
  @Input() inputmode?: string;
  @Input() autocomplete?: string;
  @Input() placeholder?: string;
  @Input() maxlength?: number;
  @Input() enterkeyhint?: string;
  @Input() hint?: string;
  /** Inline error message (what happened + what to do). */
  @Input() error?: string | null;
  /** Mono display for data fields (CNPJ, OTP, values). */
  @Input() mono = false;

  protected readonly id = `jx-field-${_uid++}`;
  protected value = '';
  protected disabled = false;

  private _onChange: (v: string) => void = () => {};
  protected onTouched: () => void = () => {};

  protected onInput(event: Event): void {
    this.value = (event.target as HTMLInputElement).value;
    this._onChange(this.value);
  }

  writeValue(value: string | null): void {
    this.value = value ?? '';
  }
  registerOnChange(fn: (v: string) => void): void {
    this._onChange = fn;
  }
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
