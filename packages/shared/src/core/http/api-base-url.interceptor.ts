import { HttpInterceptorFn } from '@angular/common/http';
import { InjectionToken, inject } from '@angular/core';

/**
 * URL absoluta do backend, prefixada em toda chamada relativa (/v1/...).
 * Vazio ('') = comportamento antigo, sem prefixo — é o caso do apps/web, que
 * roda atrás de um proxy/reverse-proxy same-origin com a API. O apps/app
 * (empacotado no APK via Capacitor) não tem same-origin nem dev-proxy em
 * produção, então precisa de uma URL absoluta (ver apps/app/src/environments).
 */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  factory: () => '',
});

export const apiBaseUrlInterceptor: HttpInterceptorFn = (req, next) => {
  const base = inject(API_BASE_URL);
  if (!base || /^https?:\/\//i.test(req.url)) {
    return next(req);
  }
  return next(req.clone({ url: `${base}${req.url}` }));
};
