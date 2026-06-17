import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from '@jaxego/core/theme/theme.service';

@Component({
  selector: 'jx-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class AppComponent {
  // Construct ThemeService at root so the signal syncs with the data-theme
  // attribute the anti-FOUC inline script already applied.
  private readonly theme = inject(ThemeService);
}
