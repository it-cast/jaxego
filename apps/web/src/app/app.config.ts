import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideZoneChangeDetection,
} from '@angular/core';
import { Routes, provideRouter, withComponentInputBinding } from '@angular/router';
import {
  provideHttpClient,
  withFetch,
  withInterceptors,
} from '@angular/common/http';
import { provideIonicAngular } from '@ionic/angular/standalone';

import { routes } from './app.routes';
import { authInterceptor } from '../core/http/auth.interceptor';
import { AuthService } from '../core/auth/auth.service';

/**
 * Build the app config for a given route map (MR-5). Each physical app
 * (admin/loja/entregador) bootstraps with its own routes via this factory; the
 * providers (http + interceptor + session restore) are identical across apps.
 */
export function makeAppConfig(appRoutes: Routes): ApplicationConfig {
  return {
    providers: [
      provideZoneChangeDetection({ eventCoalescing: true }),
      provideRouter(appRoutes, withComponentInputBinding()),
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
}

/** All-in-one `web` build config (combined routes). */
export const appConfig: ApplicationConfig = makeAppConfig(routes);
