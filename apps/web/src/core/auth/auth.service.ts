import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  ApiErrorEnvelope,
  ERROR_CODE,
  LoginErrorKind,
  LoginRequest,
  TokenPair,
} from './auth.models';

/** Result of a login attempt, mapped to UI-relevant kinds. */
export interface LoginResult {
  ok: boolean;
  kind?: LoginErrorKind;
  message?: string;
}

/**
 * AuthService — owns the access token IN MEMORY (signal). The refresh token is
 * NEVER stored here: the backend sets it as an httpOnly+Secure cookie (web), so
 * there is nothing for JS to read (XSS mitigation / senior-quality-bar Gate 8).
 *
 * No PII (email/password/token) is ever logged. Only the error `request_id`
 * (envelope) is logged for correlation (observability-production).
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly _accessToken = signal<string | null>(null);
  private readonly _role = signal<string | null>(null);

  readonly isAuthenticated = computed(() => this._accessToken() !== null);

  get accessToken(): string | null {
    return this._accessToken();
  }

  get role(): string | null {
    return this._role();
  }

  private decodeRole(token: string): string | null {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload['role'] ?? null;
    } catch {
      return null;
    }
  }

  async tryRestoreSession(): Promise<boolean> {
    try {
      const pair = await firstValueFrom(
        this.http.post<TokenPair>('/v1/auth/refresh', {}, { withCredentials: true })
      );
      this._accessToken.set(pair.access_token);
      this._role.set(this.decodeRole(pair.access_token));
      return true;
    } catch {
      return false;
    }
  }

  async login(req: LoginRequest): Promise<LoginResult> {
    try {
      const pair = await firstValueFrom(
        this.http.post<TokenPair>('/v1/auth/login', req, {
          withCredentials: true,
        })
      );
      this._accessToken.set(pair.access_token);
      this._role.set(this.decodeRole(pair.access_token));
      return { ok: true };
    } catch (err) {
      return this.mapError(err);
    }
  }

  async logout(): Promise<void> {
    try {
      await firstValueFrom(
        this.http.post('/v1/auth/logout', {}, { withCredentials: true })
      );
    } catch { /* revogação best-effort — token limpo no cliente independente */ }
    this._accessToken.set(null);
    this._role.set(null);
  }

  private mapError(err: unknown): LoginResult {
    if (err instanceof HttpErrorResponse) {
      // Network / CORS / server unreachable => status 0.
      if (err.status === 0) {
        return {
          ok: false,
          kind: 'network',
          message:
            'Sem conexão com o servidor. Verifique sua internet e tente de novo.',
        };
      }

      const envelope = err.error as ApiErrorEnvelope | undefined;
      const code = envelope?.error?.code;
      const message = envelope?.error?.message;
      const requestId = envelope?.error?.request_id;

      // Correlation only — never expose request_id raw to the user, never log PII.
      if (requestId) {
        console.warn('[auth] login failed', { code, request_id: requestId });
      }

      if (code === ERROR_CODE.TOTP_REQUIRED) {
        return { ok: false, kind: 'totp_required', message };
      }
      if (code === ERROR_CODE.ACCOUNT_LOCKED) {
        return {
          ok: false,
          kind: 'locked',
          message:
            message ??
            'Conta temporariamente bloqueada. Tente novamente mais tarde.',
        };
      }
      if (err.status >= 500) {
        return {
          ok: false,
          kind: 'server',
          message:
            'Tivemos um problema aqui. Já estamos vendo — tente em instantes.',
        };
      }
      // 401 invalid_credentials and anything else 4xx => anti-enumeration message.
      return {
        ok: false,
        kind: 'credentials',
        message:
          message ??
          'E-mail ou senha incorretos. Tente de novo ou recupere a senha.',
      };
    }

    return {
      ok: false,
      kind: 'unknown',
      message: 'Não foi possível entrar agora. Tente de novo.',
    };
  }
}
