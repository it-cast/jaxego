import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
} from '@angular/core';
import { ThemeService } from './theme.service';

/**
 * Theme toggle button. `aria-pressed` reflects the dark state; minimum 44px
 * touch target (accessibility-pro). Token-driven, no hardcoded color.
 */
@Component({
  selector: 'jx-theme-toggle',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      type="button"
      class="jx-theme-toggle"
      [attr.aria-pressed]="isDark()"
      [attr.aria-label]="label()"
      (click)="theme.toggle()"
    >
      <span aria-hidden="true">{{ isDark() ? '◑' : '◐' }}</span>
      <span class="jx-theme-toggle__text">Tema escuro</span>
    </button>
  `,
  styles: [
    `
      .jx-theme-toggle {
        display: inline-flex;
        align-items: center;
        gap: var(--jx-space-2);
        min-height: 44px;
        min-width: 44px;
        padding: var(--jx-space-2) var(--jx-space-3);
        background: var(--surface-elevated);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-full);
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-sm);
        font-weight: var(--jx-weight-semibold);
        cursor: pointer;
        transition: background-color var(--jx-motion-fast)
          var(--jx-motion-easing-out);
      }

      .jx-theme-toggle:hover {
        background: var(--surface-sunken);
      }

      .jx-theme-toggle[aria-pressed='true'] {
        border-color: var(--brand);
        color: var(--brand);
      }

      @media (prefers-reduced-motion: reduce) {
        .jx-theme-toggle {
          transition: none;
        }
      }
    `,
  ],
})
export class ThemeToggleComponent {
  protected readonly theme = inject(ThemeService);
  protected readonly isDark = computed(() => this.theme.theme() === 'dark');
  protected readonly label = computed(() =>
    this.isDark() ? 'Desativar tema escuro' : 'Ativar tema escuro'
  );
}
