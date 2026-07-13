import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/**
 * authGuard — protects surface routes. Unauthenticated (no in-memory access
 * token) users are redirected to the login of the surface they tried to reach
 * (/entrar, /equipe/entrar, /admin/entrar, /plataforma/entrar) — D-08.
 */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree([auth.loginPathForUrl(state.url)]);
};
