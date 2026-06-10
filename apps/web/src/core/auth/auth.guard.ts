import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/**
 * authGuard — protects surface routes. Unauthenticated (no in-memory access
 * token) users are redirected to /entrar (D-08). Refresh-on-load flows are
 * added in a later auth phase; here the guard is the explicit auth decision.
 */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/entrar']);
};
