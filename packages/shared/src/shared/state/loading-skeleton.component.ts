import {
  ChangeDetectionStrategy,
  Component,
  Input,
} from '@angular/core';

export type SkeletonVariant = 'line' | 'block' | 'circle';

/**
 * jx-loading-skeleton — layout-shaped loading placeholder (not a spinner).
 * UI-SPEC §4.3. aria-hidden (does not announce); the consuming container must
 * set aria-busy="true". Pulse 1.2s; disabled under prefers-reduced-motion.
 */
@Component({
  selector: 'jx-loading-skeleton',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-skeleton"
      [class.jx-skeleton--line]="variant === 'line'"
      [class.jx-skeleton--block]="variant === 'block'"
      [class.jx-skeleton--circle]="variant === 'circle'"
      [style.width]="width"
      [style.height]="height"
      aria-hidden="true"
    ></span>
  `,
  styleUrl: './loading-skeleton.component.scss',
})
export class LoadingSkeletonComponent {
  @Input() variant: SkeletonVariant = 'line';
  /** Optional explicit width (e.g. '60%', '44px'). */
  @Input() width?: string;
  /** Optional explicit height; defaults derive from the variant. */
  @Input() height?: string;
}
