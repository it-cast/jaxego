import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'jx-dots-loader',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-dots-loader">
      <div class="jx-dots">
        <span class="jx-dot"></span>
        <span class="jx-dot"></span>
        <span class="jx-dot"></span>
      </div>
    </div>
  `,
  styles: [`
    .jx-dots-loader {
      display: flex; align-items: center; justify-content: center;
      height: 80vh;
    }
    .jx-dots { display: flex; gap: 6px; }
    .jx-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--brand, #e8722a);
      animation: jx-bounce 1.2s ease-in-out infinite;
    }
    .jx-dot:nth-child(2) { animation-delay: 0.2s; }
    .jx-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes jx-bounce {
      0%, 80%, 100% { transform: scale(0.4); opacity: 0.3; }
      40% { transform: scale(1); opacity: 1; }
    }
  `],
})
export class DotsLoaderComponent {}
