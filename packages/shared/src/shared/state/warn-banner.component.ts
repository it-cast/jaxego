import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

/**
 * jx-warn-banner — non-blocking advisory (user can proceed). UI-SPEC §4.4.
 * role="status" (does not interrupt). Optional dismiss. Left border 3px
 * --warning. Copy ≤12 words first sentence (brand.md).
 */
@Component({
  selector: 'jx-warn-banner',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (!dismissed) {
      <div class="jx-warn" role="status">
        <span class="jx-warn__icon" aria-hidden="true">!</span>
        <p class="jx-warn__message">{{ message }}</p>
        @if (dismissible) {
          <button
            type="button"
            class="jx-warn__dismiss"
            aria-label="Dispensar aviso"
            (click)="onDismiss()"
          >
            ×
          </button>
        }
      </div>
    }
  `,
  styleUrl: './warn-banner.component.scss',
})
export class WarnBannerComponent {
  @Input({ required: true }) message = '';
  @Input() dismissible = false;
  @Output() dismiss = new EventEmitter<void>();

  protected dismissed = false;

  protected onDismiss(): void {
    this.dismissed = true;
    this.dismiss.emit();
  }
}
