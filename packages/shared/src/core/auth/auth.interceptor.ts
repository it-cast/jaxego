import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, from, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';

let refreshing: Promise<boolean> | null = null;

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const outgoing = attachToken(req, auth.accessToken);

  return next(outgoing).pipe(
    catchError((err) => {
      if (err instanceof HttpErrorResponse && err.status === 403) {
        const code = (err.error as { error?: { code?: string } } | undefined)?.error?.code;
        if (code === 'totp_enrollment_required') {
          void router.navigate(['/plataforma/totp-setup']);
        }
      }

      if (
        err instanceof HttpErrorResponse &&
        err.status === 401 &&
        !req.url.includes('/auth/refresh') &&
        !req.url.includes('/auth/login')
      ) {
        if (!refreshing) {
          refreshing = auth.tryRestoreSession().finally(() => { refreshing = null; });
        }
        return from(refreshing).pipe(
          switchMap((ok) => {
            if (!ok) {
              // Login da superfície onde o usuário estava (equipe/admin/plataforma/loja).
              void router.navigate([auth.loginPathForUrl(router.url)]);
              return throwError(() => err);
            }
            return next(attachToken(req, auth.accessToken));
          }),
        );
      }

      return throwError(() => err);
    }),
  );
};

function attachToken(req: Parameters<HttpInterceptorFn>[0], token: string | null) {
  return token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
}
