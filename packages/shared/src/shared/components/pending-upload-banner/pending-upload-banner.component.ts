import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/**
 * jx-pending-upload-banner — offline reassurance for queued proof photos (D-04).
 *
 * When a photo is captured offline it stays on the device and uploads on reconnect;
 * this banner reassures (NOT an error — offline-first / error-ux). `role="status"`
 * announces politely without stealing focus. The text + icon carry the meaning
 * (never colour-only). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-pending-upload-banner',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (count > 0) {
      <div class="jx-pending" role="status" aria-live="polite">
        <span class="jx-pending__icon" aria-hidden="true">{{ online ? '↻' : '☁' }}</span>
        <span class="jx-pending__text">
          @if (online) {
            Enviando {{ count }} {{ count === 1 ? 'foto' : 'fotos' }}…
          } @else {
            {{ count }} {{ count === 1 ? 'foto aguardando' : 'fotos aguardando' }} conexão — enviaremos
            quando a internet voltar.
          }
        </span>
      </div>
    }
  `,
  styleUrl: './pending-upload-banner.component.scss',
})
export class PendingUploadBannerComponent {
  /** Number of photos queued for upload. */
  @Input() count = 0;
  /** Whether the device is currently online (drives the copy). */
  @Input() online = false;
}
