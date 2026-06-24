import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  signal,
} from '@angular/core';
import { WarnBannerComponent } from '@jaxego/shared/state';

/**
 * jx-availability-toggle — online/offline switch (UI-SPEC §5, REQ-018/D-06).
 *
 * `role="switch"` + `aria-checked`; status by TEXT + position + icon, never colour
 * alone. Only an `active` courier may go online: when `disabled` (non-active) the
 * switch is inert and a jx-warn-banner explains "termine sua validação". A 409
 * from the backend (not-active) reverts the state and shows the banner. The
 * transition respects prefers-reduced-motion. Tokens only; ≥44px.
 */
@Component({
  selector: 'jx-availability-toggle',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [WarnBannerComponent],
  template: `
    <div class="jx-availability">
      <button
        type="button"
        role="switch"
        class="jx-availability__switch"
        [class.jx-availability__switch--on]="online()"
        [attr.aria-checked]="online()"
        [disabled]="disabled"
        (click)="toggle()"
      >
        <span class="jx-availability__track">
          <span class="jx-availability__thumb"></span>
        </span>
        <span class="jx-availability__label">
          {{ online() ? 'Online' : 'Offline' }}
        </span>
      </button>

      @if (disabled) {
        <jx-warn-banner
          message="Termine sua validação para ficar online e receber ofertas."
        />
        <button type="button" class="jx-availability__cta" (click)="seeValidation.emit()">
          Ver validação
        </button>
      }
    </div>
  `,
  styleUrl: './availability-toggle.component.scss',
})
export class AvailabilityToggleComponent {
  /** Non-active courier → the switch is inert and the warn-banner shows. */
  @Input() disabled = false;

  @Input() set isOnline(value: boolean) {
    this.online.set(value);
  }

  @Output() onlineChange = new EventEmitter<boolean>();
  @Output() seeValidation = new EventEmitter<void>();

  protected readonly online = signal(false);
  protected readonly liveLabel = signal('');

  protected toggle(): void {
    if (this.disabled) {
      return;
    }
    const next = !this.online();
    this.online.set(next);
    this.liveLabel.set(next ? 'Você está online' : 'Você está offline');
    this.onlineChange.emit(next);
  }

  /** Revert the optimistic state (e.g. on a 409 from the backend). */
  revert(): void {
    this.online.set(!this.online());
  }
}
