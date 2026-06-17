import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** In-app notice tone (mirrors the push moment / error-ux). */
export type NoticeTone = 'info' | 'success' | 'warning' | 'error';

/**
 * jx-notice — in-app toast that mirrors a push notification (UI-SPEC §10).
 *
 * `role="status"` (polite) so it ANNOUNCES without stealing focus (accessibility-pro
 * — a toast must never trap or move focus). Tone carries an icon + colour, but the
 * TEXT always states the message (never colour-only). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-notice',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="jx-notice"
      [class.jx-notice--success]="tone === 'success'"
      [class.jx-notice--warning]="tone === 'warning'"
      [class.jx-notice--error]="tone === 'error'"
      role="status"
      aria-live="polite"
    >
      <span class="jx-notice__icon" aria-hidden="true">{{ icon }}</span>
      <span class="jx-notice__body">
        @if (title) {
          <strong class="jx-notice__title">{{ title }}</strong>
        }
        <span class="jx-notice__message">{{ message }}</span>
      </span>
    </div>
  `,
  styleUrl: './notice.component.scss',
})
export class NoticeComponent {
  @Input() tone: NoticeTone = 'info';
  @Input() title: string | null = null;
  @Input({ required: true }) message = '';

  protected get icon(): string {
    return { info: 'ⓘ', success: '✓', warning: '⚠', error: '!' }[this.tone];
  }
}
