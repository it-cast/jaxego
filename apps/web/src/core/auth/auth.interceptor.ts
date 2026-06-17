import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.accessToken;

  const outgoing = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(outgoing).pipe(
    catchError((err) => {
      if (err instanceof HttpErrorResponse && err.status === 403) {
        const code = (err.error as { error?: { code?: string } } | undefined)?.error?.code;
        if (code === 'totp_enrollment_required') {
          void router.navigate(['/plataforma/totp-setup']);
        }
      }
      return throwError(() => err);
    }),
  );
};
