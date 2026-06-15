import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../auth/auth.service';

/**
 * Attaches the in-memory access token as `Authorization: Bearer` to API calls
 * (`/v1/*`). Without this, every authenticated request is 401: the token lived
 * in the AuthService signal but was never sent. The refresh token is a httpOnly
 * cookie carried by `withCredentials` on the auth calls — not handled here.
 *
 * Only attaches when a token exists, so public calls (login) are unaffected.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).accessToken;
  if (token && req.url.startsWith('/v1/')) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
