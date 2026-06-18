import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { IonApp } from '@ionic/angular/standalone';
import { ThemeService } from '@jaxego/core/theme/theme.service';

@Component({
  selector: 'jx-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonApp, RouterOutlet],
  template: `
    <ion-app>
      <router-outlet />
    </ion-app>
  `,
})
export class AppComponent {
  private readonly theme = inject(ThemeService);
}
