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

import { authInterceptor } from '@jaxego/core/auth/auth.interceptor';
import { AuthService } from '@jaxego/core/auth/auth.service';

/**
 * Build the app config for a given route map. Cada app físico (apps/web admin+loja,
 * apps/app entregador) faz bootstrap com suas rotas via esta factory; os providers
 * (http + interceptor + restauração de sessão) são idênticos entre os apps.
 */
export function makeAppConfig(appRoutes: Routes): ApplicationConfig {
  return {
    providers: [
      provideZoneChangeDetection({ eventCoalescing: true }),
      provideRouter(appRoutes, withComponentInputBinding()),
      provideHttpClient(withFetch(), withInterceptors([authInterceptor])),
      provideIonicAngular({ mode: 'md' }),
      // R0.5: restaura a sessão pelo cookie httpOnly antes de renderizar (sobrevive
      // a F5) e, se ok, resolve a superfície (/me) para o roteamento por papel.
      provideAppInitializer(async () => {
        const auth = inject(AuthService);
        if (await auth.tryRestoreSession()) {
          await auth.loadMe();
        }
      }),
    ],
  };
}
