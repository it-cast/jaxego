import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import {
  provideHttpClient,
  withFetch,
  withInterceptors,
} from '@angular/common/http';
import { provideIonicAngular } from '@ionic/angular/standalone';

import { routes } from './app.routes';
import { authInterceptor } from '../core/http/auth.interceptor';
import { AuthService } from '../core/auth/auth.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor])),
    provideIonicAngular({ mode: 'md' }),
    // R0.5: restore the session from the httpOnly refresh cookie before the app
    // renders, so a reload doesn't bounce an authenticated user to /entrar.
    provideAppInitializer(async () => {
      const auth = inject(AuthService);
      if (await auth.tryRefresh()) {
        await auth.loadMe();
      }
    }),
  ],
};
